# coding = utf-8
import base64
import pickle

from django_redis import get_redis_connection

def merge_cart_cookie_to_redis(request,user,response):
    """
    登录的合并购物车,将cookie中的数据合并到redis中
    :return:

     1. 数量  sku_id count   以cookie为准
     2. 勾选状态 selected    以cookie为准
    """
    # 获取cookie中的购物车数据
    cookie_cart = request.COOKIES.get('cart')
    if not cookie_cart:
        return response
    cookie_cart_dict =pickle.loads(base64.b64decode(cookie_cart.encode()))

    # 获取redis中的购物车商品数量数据,hash
    redis_conn = get_redis_connection('cart')
    redis_cart = redis_conn.hgetall('cart_%s'% user.id)

    # 用来存储redis中的最终保存的商品数量信息的hash数据
    cart = {}
    for sku_id,count in redis_cart.items():
        cart[int(sku_id)] = int(sku_id)


    redis_cart_selected_add = []  # 指明在redis中以cookie为准的勾选状态-增加
    redis_cart_selected_remove = []  # 指明在redis中以cookie为准的勾选状态-减少

    # 遍历cookie中的购物车
    # cookie_cart_dict = {
    #     sku_id_1:{
    #         'count':10,
    #         'selected':True
    #     },
    #     sku_id_2: {
    #         'count': 5,
    #         'selected': False
    #     }
    # }

    # count_selected_dict 即是cookie_cart_dict中的小字典
    # count_selected_dict = {
    #         'count':10,
    #         'selected':True
    #     },

    for sku_id,count_selected_dict in cookie_cart_dict.items():
        # 处理商品的数量 维护在redis中购物车数量的最终子字典
        cart[sku_id] = count_selected_dict['count']  # 存在即覆盖,没有添加到新的
        # 处理商品的勾选状态
        if count_selected_dict['selected']:
            # 如果cookie指明,勾选
            redis_cart_selected_add.append(sku_id)
        else:
            # 如果cookie没有指明,取消勾选
            redis_cart_selected_remove.append(sku_id)

    if cart:
        # 执行redis操作
        pl = redis_conn.pipeline()
        # 设置redis hash类型
        pl.hmset('cart_%s'% user.id,cart)
        # 设置redis set数据
        if redis_cart_selected_remove:
            pl.srem('cart_selected_%s' % user.id,*redis_cart_selected_remove)
        if redis_cart_selected_add:
            pl.sadd('cart_selected_%s' % user.id,*redis_cart_selected_add)

        pl.excute()

    # 删除cookie
        response.delete_cookie('cart')
        return response
