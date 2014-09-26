#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings

from django.conf.urls import patterns, url, include
from apps.introduction import views


urlpatterns = patterns('',
    url(r'^snapshot/$', views.SnapshotView.as_view(), name='snapshot'),
)
