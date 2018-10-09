# coding = utf-8
from django.conf.urls import url

from . import views

# from meiduo_mall.apps.users import views
urlpatterns = [
    url(r'^cart/$', views.CartsView.as_view()),  # 列表展示
    url(r'^cart/$', views.CartsView.as_view()),  # 列表展示
]
