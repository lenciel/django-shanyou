#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
import views


urlpatterns = patterns('',
    url(r'^category/list/$', views.ProductCategoryListDatatablesView.as_view(), name='productcategory_list'),
    url(r'^category/list/.json/$', views.ProductCategoryListDatatablesView.as_view(), name='productcategory_list.json', kwargs={"json": True}),
    url(r'^category/create/$', views.ProductFormView.as_view(), name='productcategory_create', kwargs={'pk': 0}),
    url(r'^category/(?P<pk>\d+)/edit/$', views.ProductFormView.as_view(), name='productcategory_edit'),
    url(r'^category/(?P<pk>\d+)/update/(?P<action_method>\w+)/$', views.ProductCategoryUpdateView.as_view(), name='productcategory_update'),
)

urlpatterns += patterns('',
   url(r'^brand/list/$', views.BrandListDatatablesView.as_view(), name='brand_list'),
   url(r'^brand/list/.json/$', views.BrandListDatatablesView.as_view(), name='brand_list.json', kwargs={'json': True}),
   url(r'^brand/create/$', views.BrandFormView.as_view(), name='brand_create', kwargs={'pk': 0}),
   url(r'^brand/(?P<pk>\d+)/edit/$', views.BrandFormView.as_view(), name='brand_edit'),
   url(r'^brand/(?P<pk>\d+)/update/(?P<action_method>\w+)/$', views.BrandUpdateView.as_view(), name='brand_update'),
)