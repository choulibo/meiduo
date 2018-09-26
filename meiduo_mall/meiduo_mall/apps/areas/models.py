from django.db import models


# Create your models here.
# 创建模型类
class Area(models.Model):
    """
    行政区划
    """
    name = models.CharField(max_length=20, verbose_name='名称')
    # 自关联 与subs反引用 自关联的外键指向自身,所以ForeignKey('self),使用related_name 指明查询的一个行政区划的所有下级单位,本模型中使用Area模型类.subs查询子集,Area模型类对象.area_set语法
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='subs', null=True, blank=True,
                               verbose_name='上级行政区划')

    class Meta:
        db_table = 'tb_areas'
        verbose_name = '行政区划'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
