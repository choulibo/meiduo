from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from .models import Area
from . import serializers


class AreasViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    pagination_class = None  # 禁止分页

    def get_queryset(self):
        """提供数据集"""
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    def get_serializer_class(self):
        """提供序列化器"""
        if self.action == 'list':
            return serializers.AreaSerializer

        else:
            return serializers.SubAreaSerializer

