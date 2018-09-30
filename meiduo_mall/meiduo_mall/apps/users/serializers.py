# coding = utf-8
# from . models import User
import re

from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from goods.models import SKU
from .models import User, Address
from . import constants


class CreateUserSerializer(serializers.ModelSerializer):
    """创建用户的序列化器"""
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)
    token = serializers.CharField(label='JWT token', read_only=True)  # 返回给前端,只需要序列化执行

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'password2', 'mobile', 'sms_code', 'allow', 'token']
        extra_kwargs = {
            "username": {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            },
            'password': {
                'write_only': True,
                # 'write_length': '仅允许8-20个字符的密码',
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    def validate_mobile(self, value):
        """验证手机号"""
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')

        return value

    def validate_allow(self, value):
        if value != 'true':
            raise serializers.ValidationError('请注意用户协议')

        return value

    def validate(self, data):
        """判断两次密码"""
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')

        redis_conn = get_redis_connection('verify_codes')
        mobile = data['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')

        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return data

    def create(self, validated_data):
        """重写create方法,增加秘密的加密"""
        # validate_data 包含了用不到的数据,所以删除用不到的数据
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        # user = User.objects.create(**validated_data)
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()

        # 签发jwt token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        user.token = token

        return user


class UserAddressSerializer(serializers.ModelSerializer):
    """
    用户地址序列化器
    """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def validate_mobile(self, value):
        """
        验证手机号
        """
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def create(self, validated_data):
        """
        保存
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    """
    地址标题
    """

    class Meta:
        model = Address
        fields = ('title',)


class AddUserBrowsingHistorySerializer(serializers.Serializer):
    sku_id = serializers.IntegerField(label="商品SKU编号", min_value=1)

    def validate_sku_id(self, value):
        """
        检验sku_id是否存在
        """
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('该商品不存在')
        return value

    def create(self, validated_data):
        # sku_id
        sku_id = validated_data['sku_id']

        # user_id
        user = self.context['request'].user

        # redis  [6, 1,2,3,4,5]
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()

        redis_key = 'history_%s' % user.id
        # 去重
        pl.lrem(redis_key, 0, sku_id)

        # 保存 增加
        pl.lpush(redis_key, sku_id)

        # 截断
        pl.ltrim(redis_key, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT-1)

        pl.execute()

        return validated_data


class SKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'comments')

