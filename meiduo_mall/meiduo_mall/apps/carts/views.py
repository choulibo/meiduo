from django.shortcuts import render

# Create your views here.
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from .serializers import CartSerializer
from django_redis import get_redis_connection
import pickle
import base64
from . import constants


class CartsView(GenericAPIView):
    """购物车"""
    serializer_class = CartSerializer

    def perform_authentication(self, request):
        """执行具体的请求方法的身份认证关掉,由视图自己来进行身份认证"""
        pass

    def post(self, request):
        """保存购物车"""
        # 保存字段 sku_id   count selected

        # 进行校验
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data['sku_id']
        count = serializer.validated_data['count']
        selected = serializer.validated_data['selected']

        # 判断用户是否登录,如果是登录用户保存到redis中
        try:
            user = request.user
        except Exception:
            user = None

        # 保存
        if user and user.is_authenticated:
            # 如果用户登录,保存到redis中
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()

            # 用户购物车数据 ,保存在redis中 hash
            pl.hincrby('cart_%s' % user.id, sku_id, count)

            # 用户勾选数据 保存在redis中,set
            if selected:
                pl.sadd('cart_seleted_%s' % user.id, sku_id)

            pl.execute()
            return Response(serializer.data)
        else:
            # 如果没有登录.保存到cookie中  response = Response()  response.set_cookie
            # 取出cookie中的数据
            cart_str = request.COOKIES.get('cart')

            if cart_str:
                # 解析
                cart_str = cart_str.decode()  # bytes类型
                cart_bytes = base64.b64decode(cart_str)  # base64需要传入bytes类型
                cart_dict = pickle.loads(cart_bytes)  # 字典类型

            else:
                cart_dict = {}

            # 保存,在保存之前,判断购物车中是否有商品,即是不是第一次加入购物车
            if sku_id in cart_dict:
                # 如果商品存在购物车中，累加
                cart_dict[sku_id]['count'] += count
                cart_dict[sku_id]['selected'] = selected
            else:
                # 如果商品不在购物车中，设置,第一次保存到购物车中
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': selected
                }

            cart_cookie = base64.b64encode(pickle.dumps(cart_dict)).decode()

            # 设置cookie
            response = Response(serializer.data)
            response.set_cookie('cart', cart_cookie, max_age=constants.CART_COOKIE_EXPIRES)

            return response