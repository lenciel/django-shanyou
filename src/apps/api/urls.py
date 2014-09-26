#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings

from django.conf.urls import patterns, url, include
from apps.api.views import *


urlpatterns = patterns('',
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^docs/', include('rest_framework_swagger.urls')),
    )
