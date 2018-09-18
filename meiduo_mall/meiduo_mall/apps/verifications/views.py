from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from . import constants


class ImageCodeView(APIView):
    """图片验证码"""

    def get(self, request, image_code_id):
        # 生成验证码图片
        text, image = captcha.generate_captcha()

        # 保存真实值
        redis_conn = get_redis_connection('verify_codes')  # 获取连接对象
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 返回图片
        return HttpResponse(image, content_type='image/jpg')
