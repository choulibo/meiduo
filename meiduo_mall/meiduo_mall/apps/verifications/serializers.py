# coding = utf-8
from rest_framework import serializers
from django_redis import get_redis_connection


class ImageCodeCheckSerializer(serializers.Serializer):
    """图片验证码校验序列化器"""

    image_code_id = serializers.UUIDField()
    text = serializers.CharField(max_length=4, min_length=4)  # 只能是4位

    def validate(self, attrs):
        image_code_id = attrs['image_code_id']
        text = attrs['text']  # 用户输入的验证码内容

        # 查询真实图片验证码
        # 创建连接对象
        redis_conn = get_redis_connection('verify_codes')
        # 获取验证码内容
        real_image_code_text = redis_conn.get('img_%s' % image_code_id)
        if not real_image_code_text:  # 没取到
            raise serializers.ValidationError('图片验证码无效')

        # 删除redis中的图片验证码  可以在验证码比较前进行删除,以为已经保存在 real_image_code_text中了
        redis_conn.delete("img_%s" % image_code_id)

        real_image_code_text = real_image_code_text.decode()  # 把bytes类型转换成字符串
        if real_image_code_text.lower() != text.lower():  # redis中的验证码与用户输入发不匹配
            raise serializers.ValidationError('图片验证码错误')
        # 判断是否在60秒内

        mobile = self.context['view'].kwargs['mobile']  # context['view'] 获取类对象,kwargs['mobile']类对象的属性,在序列化的时候,mobile等弄进去kwargs
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            raise serializers.ValidationError('请求次数过于频繁')

        return attrs
