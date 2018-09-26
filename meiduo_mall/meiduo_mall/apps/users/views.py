from django.shortcuts import render

# Create your views here.
from rest_framework import mixins
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework.views import APIView

# from meiduo_mall.apps.users.models import User
from rest_framework.viewsets import GenericViewSet

from users import serializers
from users.serializers import CreateUserSerializer
from .models import User


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


class AddressViewSet(mixins.CreateModelMixin,mixins.UpdateModelMixin,GenericViewSet):
    """用户地址新增与修改"""
    serializer_class = serializers.UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_delete = False)


        # GET /addresses/
    def list(self,request,*args,**kwargs):
        """用户地址列表数据"""
        queryset = self.get_queryset()

        serializer = self.get_serializer(queryset,many = True)
        user = self .request.user
        return Response({
            'user_id':user.id,
            'default_addresses_id':user.default_address_id
        })























