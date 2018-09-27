# coding = utf-8
from django.conf.urls import url
from rest_framework import routers

from . import views
from rest_framework_jwt.views import obtain_jwt_token
# from meiduo_mall.apps.users import views
urlpatterns = [
    url(r'^users/$', views.UserView.as_view()),
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    url(r'^authorizations/$',obtain_jwt_token),  # 登录认证
]


router = routers.DefaultRouter()
router.register(r'addresses',views.AddressViewSet.as_view, base_name='addresses')