# coding = utf-8
# from . models import User
from rest_framework import serializers
import re
from django_redis import get_redis_connection

from users.models import User


class CreateUserSerialzier(serializers.ModelSerializer):
    """创建用户的序列化器"""
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)

    # token = serializers.CharField(label=)




    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'password2', 'mobile', 'sms_code', 'allow']
        extra_kwargs = {
            "username": {
                'min_length': 5,
                'max_length': 20,
                'error_message': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码'
                }
            },
            'password': {
                'write_only': True,
                'write_length': '仅允许8-20个字符的密码',
                'min_length': 8,
                'max_length': 20,
                'error_message': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码'

                }
            }
        }

    def valid_mobile(self, value):
        """验证手机号"""
        if not re.match(r'^1[3-9]\d{9}', value):
            raise serializers.ValidationError('手机号格式错误')

        return value

    def validate_allow(self, value):
        if value != 'true':
            raise serializers.ValidationError('请注意用户协议')

        return value

    def validate(self, data):
        """判断两次密码"""
        if data['password'] != data['password']:
            raise serializers.ValidationError('两次密码不一致')

        redis_conn = get_redis_connection('verify_codes')
        mobile = data['mobile']

        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')

        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return data

    def create(self, validate_data):
        """重写create方法,增加秘密的加密"""
        # validate_data 包含了用不到的数据,所以删除用不到的数据
        del validate_data['password']
        del validate_data['sms_code']
        del validate_data['allow']

        # user = User.objects.create(**validate_data)
        user = super().create(validate_data)
        user.set_password(validate_data['password'])
        user.save()
        return user






























