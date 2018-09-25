# # coding = utf-8
# import urllib.parse
#
# from django.conf import settings
#
#
# class OAuthQQ(object):
#     """
#     QQ认证辅助工具类
#     """
#     # 实例属性
#     def __init__(self, client_id=None, redirect_uri=None, state=None):
#         self.client_id = client_id if client_id else settings.QQ_CLIENT_ID
#         self.redirect_uri = redirect_uri if redirect_uri else settings.QQ_REDIRECT_URI
#         self.state = state or settings.QQ_STATE  # 和上边效果一致
#     # 获取url的方法
#     def get_qq_login_url(self):
#         url = 'https://graph.qq.com/oauth2.0/authorize?'
#         params = {
#             'response_type': 'code',
#             'client_id': self.client_id,
#             'redirect_uri': self.redirect_uri,
#             'state': self.state,
#             'scope': 'get_user_info',
#         }
#         # 将query字典转换为url路径中的查询字符串拼接
#         url += urllib.parse.urlencode(params)
#         return url

from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer, BadData
# from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings
import json
import logging

# from . import constants
from . import constants
from .exceptions import OAuthQQAPIError

logger = logging.getLogger('django')


class OAuthQQ(object):
    """
    QQ认证辅助工具类
    """

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, state=None):
        self.client_id = client_id or settings.QQ_CLIENT_ID
        self.client_secret = client_secret or settings.QQ_CLIENT_SECRET
        self.redirect_uri = redirect_uri or settings.QQ_REDIRECT_URI
        self.state = state or settings.QQ_STATE  # 用于保存登录成功后的跳转页面路径

    def get_qq_login_url(self):
        """
        获取qq登录的网址
        :return: url网址
        """
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state,
            'scope': 'get_user_info',
        }
        url = 'https://graph.qq.com/oauth2.0/authorize?' + urlencode(params)
        return url

    def get_access_token(self, code):
        url = 'https://graph.qq.com/oauth2.0/token?'
        params = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri,
        }
        url += urlencode(params)
        try:
            # 发送请求
            resp = urlopen(url)

            # 读取响应体数据
            resp_data = resp.read()  # bytes
            resp_data = resp_data.decode()  # str

            # access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14

            # 解析 access_token
            resp_dict = parse_qs(resp_data)
        except Exception as e:
            logger.error('获取access_token异常:%s' % e)
            raise OAuthQQAPIError  # 抛出异常
        else:
            access_token = resp_dict.get('access_token')

            return access_token[0]

    def get_openid(self, access_token):
        url = 'https://graph.qq.com/oauth2.0/me?access_token='+ access_token

        try:
            # 发送请求
            resp = urlopen(url)

            # 读取响应体数据
            resp_data = resp.read()  # bytes
            resp_data = resp_data.decode()  # str

            # 解析
            resp_data = resp_data[10:-4]
            resp_dict = json.loads(resp_data)

        except Exception as e:
            logger.error("获取openid异常:%s" % e)
            raise OAuthQQAPIError

        else:
            openid = resp_dict.get('openid')
            return openid

    def generate_bind_user_access_token(self, openid):
        serializer = TJWSSerializer(settings.SECRET_KEY, constants.BIND_USER_ACCESS_TOKEN_EXPIRES)
        token = serializer.dumps({'openid': openid})
        return token.decode()

    @staticmethod
    def check_bind_user_access_token(access_token):
        serializer = TJWSSerializer(settings.SECRET_KEY, constants.BIND_USER_ACCESS_TOKEN_EXPIRES)
        try:
            data = serializer.loads(access_token)
        except BadData:
            return None
        else:
            return data['openid']
