from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.mainpage, name="mainpage"),
    url(r'^intro/$', views.introduction, name="introduction"),
    url(r'^dataimport/$', views.dataimport, name="dataimport"),
    url(r'^data_confirm/(?P<pk>\d+)/$', views.data_confirm, name="data_confirm"),
]
