import os
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import OrderInfo
from  alipay import AliPay
from django.conf import settings


class PaymentView(APIView):
    """
    获取支付链接
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        user = request.user
        # order_id
        # 校验
        try:
            order = OrderInfo.objects.get(
                order_id=order_id,
                user=user,  # 那个用户
                status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'],  # 订单状态
                pay_method=OrderInfo.PAY_METHODS_ENUM['ALIPAY']  # 支付方式
            )
        except OrderInfo.DoesNotExist:
            return Response({'message': '订单信息有误'}, status=status.HTTP_400_BAD_REQUEST)


            # 向支付宝发起请求
        alipay_client = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False 是否是沙箱环境
        )

        # 构造支付宝支付链接地址
        # 电脑网站支付，需要跳转到https://openapi.alip7ay.com/gateway.do? + order_string
        order_string = alipay_client.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单编号
            total_amount=str(order.total_amount),  # 总金额
            subject='美多商城订单%s' % order_id,
            return_url="http://www.meiduo.site:8080/pay_success.html",
            notify_url=None  # 可选, 不填则使用默认notify url
        )
        # 拼接支付链接
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        # 返回
        return Response({'alipay_url':alipay_url})
