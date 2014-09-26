#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
    url(r'^$', 'apps.website.views.index', name='index'),
    url(r'^legal$', 'apps.website.views.legal', name='legal'),
    url(r'^privacy$', 'apps.website.views.privacy', name='privacy'),
)

urlpatterns += patterns('',
    url(r'^introduction/', include('apps.introduction.urls', namespace='introduction')),
)
