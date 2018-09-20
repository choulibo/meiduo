from django.shortcuts import render

# Create your views here.
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

# from meiduo_mall.apps.users.models import User
from .serializers import CreateUserSerialzier
from .models import User


class UserView(CreateAPIView):
    """
    用户注册
    传入参数:
    username,password,password2,sms_code,mobile,allow
    """
    serializer = CreateUserSerialzier


class UserCountView(APIView):
    """
    用户数量
    """

    def get(self, request, username):
        """
        获取指定用户的数量
        :param request:
        :param username:
        :return:
        """
        count = User.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count
        }

        return Response(data)


class MobileCountView(APIView):
    """手机号数量"""

    def get(self, request, mobile):
        """
        获取手机号数量
        :param request:
        :param mobile:
        :return:
        """
        count = User.objects.filter(mobile=mobile).count()
        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)
