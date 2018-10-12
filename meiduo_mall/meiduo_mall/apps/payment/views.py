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

from payment.models import Payment


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


# http://www.meiduo.site:8080/pay_success.html?
# charset=utf-8
# &out_trade_no=20181012105247000000003
# &method=alipay.trade.page.pay.return
# &total_amount=6776.00
# &sign=B4AlD%2FqOp9DTyJIB6Tgg5yIUyttcclQNIOwsAyuZOvlBWjGZ6k%2BUnSTQ7z%2BmJquJj4LkeeXJiKLt9aGFgSfKNKasLVIls8Tl4qJaxSpFyKGNq5HnHslk6t92ZrpKSW3PZSE4KCyRZcnxhuIvPOYTRMcz%2FoAMKbrxm8tlBYLwGG%2FdApHk8Q8zpbQRtReWCd1FcBXOWmb%2FzWq%2FrHMk27GFNMQhZbf3MSrpICa9iafgde9e54DIXVPo665Y15tG7iDxNkiRPsN3aIhEHDl6Xu00TKvF9DaDN2BA5C4s6AVAHFD73uRYuN0LBt0SzBuTUCxALWbfrMd5OMLBYJJhI8mn6A%3D%3D&trade_no=2018101222001401740501032600
# &auth_app_id=2016092100560523
# &version=1.0
# &app_id=2016092100560523
# &sign_type=RSA2
# &seller_id=2088102176579703
# &timestamp=2018-10-12+19%3A00%3A34


 # PUT /payment/status/?支付宝参数
class PaymentStatusView(APIView):
    """保存支付结果"""
    def put(self,request):
        # 接受参数
        # 校验
        alipay_req_data = request.query_params  # QueryDict
        if not alipay_req_data:
            return Response({'message':'缺少参数'},status = status.HTTP_400_BAD_REQUEST)
        alipay_req_dict = alipay_req_data.dict()
        sign = alipay_req_dict.pop('sign')
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

        # 返回验证结果， True False
        # 是不是支付宝
        result = alipay_client.verify(alipay_req_dict,sign)

        if result:
            order_id = alipay_req_dict.get('out_trade_no')
            trade_id = alipay_req_dict.get('trade_no')

            # 保存数据
            # 保存支付结果数据Payment
            Payment.objects.create(
                order_id = order_id,
                trade_id = trade_id
            )

            # 修改订单状态
            OrderInfo.objects.filter(order_id = order_id).update(status = OrderInfo.ORDER_STATUS_ENUM['UNSEND'])
            return Response({'trade_id':trade_id})
        else:
            return Response({'message':'参数有误'},status = status.HTTP_400_BAD_REQUEST)








