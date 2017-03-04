from django.views.generic import TemplateView
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.mainpage, name="mainpage"),
    url(r'^intro/$', views.introduction, name="introduction"),
    url(r'^dataimport/$', views.dataimport, name="dataimport"),
    url(r'^data_confirm/(?P<pk>\d+)/$', views.data_confirm, name="data_confirm"),
    url(r'^data_process/(?P<pk>\d+)/$', views.data_process, name="data_process"),
    url(r'^data_summary/(?P<pk>\d+)/$', views.data_summary, name="data_summary"),
    url(r'^data_reassessment1/(?P<pk>\d+)/$', views.data_reassessment1, name="data_reassessment1"),
    url(r'^data_reassessment2/(?P<pk>\d+)/$', views.data_reassessment2, name="data_reassessment2"),
    url(r'^final_result/(?P<pk>\d+)/$', views.final_result, name="final_result"),
    url(r'^export_delete/(?P<pk>\d+)/$', views.export_delete, name="export_delete"),
    url(r'^contact_us/', TemplateView.as_view(template_name="calcmain/contact_us.html"), name='contact_us'),
    url(r'^mail_complete/', TemplateView.as_view(template_name="calcmain/mail_complete.html"), name='mail_complete'),
]
