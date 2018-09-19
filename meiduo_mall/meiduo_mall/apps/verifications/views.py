import random
from unittest import result

from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response

from meiduo_mall.utils.exceptions import logger
from meiduo_mall.utils.yuntongxun.sms import CCP
from .serializers import ImageCodeCheckSerializer
# Create your views here.

from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from . import constants

from celery_tasks.sms.tasks import send_sms_code
import logging

logger = logging.getLogger('django')


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


class SMSCodeView(GenericAPIView):
    """短信验证码
    传入参数:
    mobile  image_code_id ,text
    """
    serializer_class = ImageCodeCheckSerializer

    def get(self, request, mobile):
        # 1.校验参数 由序列化器完成
        serializer = self.get_serializer(data=request.query_params)  # 反序列化 query_params = request.GET
        serializer.is_valid(raise_exception=True)
        # 2.生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        # 3.保存验证码  保存发送记录
        redis_conn = get_redis_connection('verify_codes')  # 创建 redis连接对象
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

         # redis管道
        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()

        # 4.发送短信
        # try:
        #     ccp = CCP()  # 获取对象
        #     expires = constants.SMS_CODE_REDIS_EXPIRES // 60  # 验证码的有效时间,单位分钟
        #     result = ccp.send_template_sms(mobile, [sms_code, expires], constants.SMS_CODE_TEMP_ID)
        # except Exception as e:
        #     logger.error("发送短信验证码信息[异常][mobile:%s,message:%s]" % (mobile, e))
        #     return Response({'message': "failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        #     # 返回
        # else:
        #     if result == 0:
        #         logger.info("发送验证码短信[正常][mobile:%s] " % mobile)
        #         return Response({"message":"OK"})
        #     else:
        #         logger.warning("发送验证码短信[失败][mobile:%s]"% mobile)
        #         return Response({'message':"failed"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        expires = constants.SMS_CODE_REDIS_EXPIRES // 60
        send_sms_code.delay(mobile,sms_code,expires,constants.SMS_CODE_TEMP_ID)

        return Response({"message":"OK"})