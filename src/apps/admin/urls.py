#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings

from django.conf.urls import patterns, url, include
from apps.admin.views import ExcelCenterView


urlpatterns = patterns('',
    url(r'^$', 'apps.admin.views.home', name='admin_home'),
    url(r'^system/$', 'apps.admin.views.system', name='system'),
    url(r'^dashboard/$', 'apps.admin.views.dashboard', name='dashboard'),
    url(r'^foundation/', include('apps.foundation.urls', namespace='foundation')),
    url(r'^account/', include('apps.account.urls', namespace='account')),
    url(r'^initdata/$', 'apps.admin.views.initdata'),
    url(r'^excel/$', ExcelCenterView.as_view(), name="excel_export_center")
)

urlpatterns += patterns('',
   url(r'^catalog/', include('apps.catalog.urls', namespace='catalog')),
   url(r'^customer/', include('apps.customer.urls', namespace='customer')),
   url(r'^project/', include('apps.project.urls', namespace='project')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^loaddata/(?P<filename>.*)', 'apps.admin.views.loaddata'),
    )
