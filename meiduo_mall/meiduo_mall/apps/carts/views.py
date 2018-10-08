from django.shortcuts import render

# Create your views here.
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from goods.models import SKU
from .serializers import CartSerializer, CartSKUSerializer
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
                cart_str = cart_str.encode()  # bytes类型
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

    def get(self, request):
        """查询购物车"""
        # 判断购物车登录状态
        try:
            user = request.user
        except Exception:
            user = None

        # 如果用户登录,从redis中查询
        if user and user.is_authenticated:
            # 从redis中查询 1.sku_id count  2.selected
            redis_conn = get_redis_connection('cart')
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)
            redis_cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)
            # redis_cart = {
            #     商品sku_id bytes字节类型 : 数量 bytes字节类型
            #     商品sku_id bytes字节类型 : 数量 bytes字节类型
            #     商品sku_id bytes字节类型 : 数量 bytes字节类型
            #      .....
            # }
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_cart_selected
                }

        else:
            # 如果用户未登录,从cookie中查询
            cookie_cart = request.COOKIES.get('cart')

            if cookie_cart:
                # 表示cookie中有购物车数据
                # 解析  和保存的状态相反取出
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            else:
                # 表示cookie中没有购物车数据
                cart_dict = {}
        # 查询数据库
        sku_id_list = cart_dict.keys()  # 所有商品收到sku_id
        sku_obj_list = SKU.objects.filter(id__in = sku_id_list)   # 取出所有商品对象,用于返回数据

        # 在sku_id对象中的模型类只有id属性,所以要在对象中添加count和selected属性
        # 对所有对象遍历
        for sku in sku_obj_list:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        # 序列化数据返回
        serializer = CartSKUSerializer(sku_obj_list,many=True)
        return Response(serializer.data)