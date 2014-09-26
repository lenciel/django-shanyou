#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url, include
from apps.customer import views


urlpatterns = patterns('',
    url(r'^customer/list/$', views.CustomerListDatatablesView.as_view(), name='customer_list'),
    url(r'^customer/list/.json/$', views.CustomerListDatatablesView.as_view(), name='customer_list.json', kwargs={'json': True}),
    url(r'^customer/list/.excel/$', views.CustomerListExcelView.as_view(), name='customer_list.excel'),
    url(r'^customer/create/$', views.CustomerFormView.as_view(), name='customer_create', kwargs={"pk": 0}),
    url(r'^customer/(?P<pk>\d+)/edit/$', views.CustomerFormView.as_view(), name='customer_edit'),
    url(r'^customer/(?P<pk>\d+)/delete/$', views.CustomerDeleteView.as_view(), name='customer_delete'),
    url(r'^(?P<pk>\d+)/$', views.CustomerDetailView.as_view(), name='customer_detail'),
    url(r'^customer/(?P<pk>\d+)/project/list/.json/$', views.CustomerProjectListDatatablesView.as_view(), name='customer_project_list', kwargs={'json': True}),
)

urlpatterns += patterns('',
    url(r'^partner/list/$', views.PartnerListDatatablesView.as_view(), name='partner_list'),
    url(r'^partner/list/.json/$', views.PartnerListDatatablesView.as_view(), name='partner_list.json', kwargs={'json': True}),
    url(r'^partner/list/.excel/$', views.PartnerListExcelView.as_view(), name='partner_list.excel'),
    url(r'^partner/create/$', views.PartnerFormView.as_view(), name='partner_create', kwargs={"pk": 0}),
    url(r'^partner/(?P<pk>\d+)/edit/$', views.PartnerFormView.as_view(), name='partner_edit'),
    url(r'^partner/(?P<pk>\d+)/delete/$', views.PartnerDeleteView.as_view(), name='partner_delete'),
    url(r'^partner/(?P<pk>\d+)/$', views.PartnerDetailView.as_view(), name='partner_detail'),
    url(r'^partner/(?P<pk>\d+)/customer/list/.json/$', views.PartnerCustomerListDatatablesView.as_view(), name='partner_customer_list', kwargs={'json': True}),
)

urlpatterns += patterns('',
    url(r'^partner/(?P<pk>\d+)/tracking/list/.json/$', views.PartnerTrackingListDatatablesView.as_view(), name='partnertracking_list', kwargs={'json': True}),
    url(r'^partner/tracking/(?P<pk>\d+)/edit/$', views.PartnerTrackingFormView.as_view(), name='partnertracking_edit'),
    url(r'^partner/tracking/create/$', views.PartnerTrackingFormView.as_view(), name='partnertracking_create', kwargs={'pk': 0}),
)