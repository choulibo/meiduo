# coding:utf-8
from email.policy import HTTP

from django.shortcuts import render

# Create your views here.
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, GenericAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework.views import APIView

# from meiduo_mall.apps.users.models import User
from rest_framework.viewsets import GenericViewSet
from rest_framework_jwt.views import ObtainJSONWebToken

from . import serializers
from .serializers import CreateUserSerializer
from .models import User
from . import constants
from django_redis import get_redis_connection
from goods.models import SKU
from carts.utils import merge_cart_cookie_to_redis


class UserView(CreateAPIView):
    """
    用户注册
    传入参数：
        username, password, password2, sms_code, mobile, allow
    """
    serializer_class = serializers.CreateUserSerializer


class UsernameCountView(APIView):
    """
    用户名数量
    """

    def get(self, request, username):
        """
        获取指定用户名数量
        """
        count = User.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count
        }

        return Response(data)


# url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
class MobileCountView(APIView):
    """
    手机号数量
    """

    def get(self, request, mobile):
        """
        获取指定手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()

        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)


class UserDetailView(RetrieveAPIView):
    """用户基本信息"""
    serializer_class = serializers.UserDetailSerializer
    # queryset = User.objects.all()
    permission_classes = [IsAuthenticated]  # 权限认证

    def get_object(self):
        """返回当前请求的用户"""
        # 在类视图对象中,,可以通过类视图对象属性获取request
        # 在django的请求request对象中,user属性表明当前请求的用户
        return self.request.user


class EmailView(UpdateAPIView):
    """保存邮箱"""
    serializer_class = serializers.EmailSerializer
    permission_classes = [IsAuthenticated]

    # 重写get_objects方法来获取具体的PK值
    def get_object(self, *args, **kwargs):
        return self.request.user


class VerifyEmailView(APIView):
    """
    邮箱验证
    """

    def get(self, request):
        # 获取token
        token = request.query_params.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)

        # 验证token
        user = User.check_verify_email_token(token)
        if user is None:
            return Response({'message': '链接信息无效'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.email_active = True
            user.save()
            return Response({'message': 'OK'})


class AddressViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    """用户地址新增与修改"""
    serializer_class = serializers.UserAddressSerializer
    permissions = [IsAuthenticated]

    # url 是(r'^username/(?P<username>\w{5,20})/count/$'),views.UsernameCountView.asview()
    def get_queryset(self):
        return self.request.user.addresses.filter(is_delete=False)

    # GET /addresses/
    def list(self, request, *args, **kwargs):
        """用户地址列表数据"""
        queryset = self.get_queryset()

        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_addresses_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializers.data,
        })

    # POST /addresses/
    def create(self, request, *args, **kwargs):
        """保存用户地址数据"""
        # 保存用户地址数据数目不能超过上限
        # 在保存数据之前进行验证数据
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': "保存地址数据已达上限"})

        return super().create(request, *args, **kwargs)

    def destory(self, request, *args, **kwargs):
        """处理删除"""
        # 获取对象
        address = self.get_object()
        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        # 204 表示删除成功
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """设置默认地址"""
        # 获取对象
        address = self.get_object()
        # 将对象保存到
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """修改标题"""
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserBrowsingHistoryView(CreateAPIView):
    """
    用户浏览历史记录
    """
    serializer_class = serializers.AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    # request对象
    def get(self, request):
        # user_id
        user_id = request.user.id

        # 查询redis  list
        redis_conn = get_redis_connection('history')
        print('1')
        # 是一个列表
        sku_id_list = redis_conn.lrange('history_%s' % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT - 1)

        # 数据库 这样查询出的数据没有顺序
        # sku_object_list = SKU.objects.filter(id__in=sku_id_list)

        skus = []
        for sku_id in sku_id_list:
            sku = SKU.objects.get(id=sku_id)
            skus.append(sku)

        # 序列化 返回
        print('2')
        serializer = serializers.SKUSerializer(skus, many=True)
        return Response(serializer.data)


class UserAuthorizeView(ObtainJSONWebToken):
    """用户登录认证视图"""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        # 如果用户登录成功,合并购物车
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            response = merge_cart_cookie_to_redis(request, user, response)
        return response
