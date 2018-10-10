from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings
from .serializer import OAuthQQUserSerializer
from .models import OAuthQQUser
from .utils import OAuthQQ
from .exceptions import OAuthQQAPIError
from carts.utils import merge_cart_cookie_to_redis

class QQAuthURLView(APIView):
    """
    获取QQ登录的url        ?next=xxx
    """

    def get(self, request):
        """获取next参数"""
        next = request.query_params.get('next')
        # 拼接QQ登录的网址
        # 实例化
        oauth_qq = OAuthQQ(state=next)
        login_url = oauth_qq.get_qq_login_url()
        return Response({'login_url': login_url})

    # def post(self,request):  # 放进序列化器里边
    #     # 获取数据
    #
    #     # 校验数据
    #
    #     # 判断用户是否存在
    #     # 如果存在,绑定,创建OAuthQQUser数据
    #
    #     # 如果不存在,先创建User,创建OAuthQQUser数据
    #
    #     # 签发JWT token


class QQAuthUser(CreateAPIView):
    """
    QQ登录的用户  ?code = xxx
    """
    serializer_class = OAuthQQUserSerializer

    def get(self, request):
        """获取code"""
        code = request.query_params.get('code')

        if not code:
            return Response({'messages': '缺少code'}, status=status.HTTP_400_BAD_REQUEST)

        # 凭借code 获取access_token
        oauth_qq = OAuthQQ()
        try:
            # 凭借access_token 获取openid
            access_token = oauth_qq.get_access_token(code)
            openid = oauth_qq.get_openid(access_token)
        except OAuthQQAPIError:
            return Response({'messages': '访问qq借口异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            oauth_qq_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果数据不存在，处理openid 并返回
            access_token = oauth_qq.generate_bind_user_access_token(openid)
            return Response({'access_token': access_token})
        else:

            # 如果数据存在,表示用户已经绑定过身份,签发JWT token
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            user = oauth_qq_user.user
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            # return Response({
            #     'username':user.username,
            #     'user_id':user.id,
            #     'token':token,
            # })
            # 绑定过直接登录
            response = Response({
                'username':user.username,
                'user_id':user.id,
                'token':token,
            })
            response = merge_cart_cookie_to_redis(request,user,response)
            return response
    #
    # def post(self,request):
    #     """
    #     保存QQ登录用户数据
    #     :param request:
    #     :return:
    #     """
    #
    #     serializer = self.get_serializer(data = request.data)
    #     serializer.is_valid(raise_exception= True)
    #     user = serializer.save()
    #
    #     # 生成已登录的token
    #     jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    #     jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
    #
    #     payload = jwt_payload_handler(user)
    #     token = jwt_encode_handler(payload)
    #
    #     response = Response({
    #         'token': token,
    #         'user_id': user.id,
    #         'username': user.username
    #     })
    #
    #     return response

    # 重写post方法
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        # 合并购物车
        user = self.user
        response = merge_cart_cookie_to_redis(request, user, response)

        return response



















