#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
import views


urlpatterns = patterns('',
    url(r'^image/upload$', views.upload_image_view)
)

urlpatterns += patterns('',
    url(r'^clientapp/list$', views.ClientAppListDatatablesView.as_view(), name='clientapp_list'),
    url(r'^clientapp/list.json', views.ClientAppListDatatablesView.as_view(), name='clientapp_list.json', kwargs={'json': True}),
    url(r'^clientapp/create$', views.ClientAppFormView.as_view(), name='clientapp_create', kwargs={'pk': 0}),
    url(r'^clientapp/(?P<pk>\d+)/edit$', views.ClientAppFormView.as_view(), name='clientapp_edit'),
    url(r'^clientapp/(?P<pk>\d+)/delete$', views.ClientAppDeleteView.as_view(), name='clientapp_delete'),
)
