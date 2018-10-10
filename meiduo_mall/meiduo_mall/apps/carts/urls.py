# coding = utf-8
from django.conf.urls import url

from . import views

# from meiduo_mall.apps.users import views
urlpatterns = [
    url(r'^cart/$', views.CartView.as_view()),  # 列表展示
    url(r'^cart/selection/$', views.CartSelectAllView.as_view()),  # 列表展示
]
