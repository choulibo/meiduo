# coding = utf-8
from django.conf.urls import url
from rest_framework import routers

from . import views
from rest_framework_jwt.views import obtain_jwt_token
# from meiduo_mall.apps.users import views
urlpatterns = [
    url(r'^categories/(?P<category_id>\d+)/skus/$',views.SKUListView.as_view()),  # 列表展示

]
