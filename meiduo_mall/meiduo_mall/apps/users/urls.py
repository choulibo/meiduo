# coding = utf-8
from django.conf.urls import url
from . import views

# from meiduo_mall.apps.users import views

urlpatterns = [
    url(r'^users/$', views.UserView.as_view())
]
