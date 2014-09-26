#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from apps.project import views


urlpatterns = patterns('',
    url(r'^project/list/$', views.ProjectListDatatablesView.as_view(), name='project_list'),
    url(r'^project/list/.json/$', views.ProjectListDatatablesView.as_view(), name='project_list.json', kwargs={"json": True}),
    url(r'^project/list/.excel/$', views.ProjectListExcelView.as_view(), name='project_list.excel'),
    url(r'^project/create/$', views.ProjectFormView.as_view(), name='project_create', kwargs={"pk": 0}),
    url(r'^project/(?P<pk>\d+)/edit/$', views.ProjectFormView.as_view(), name='project_edit'),
    url(r'^project/(?P<pk>\d+)/delete/$', views.ProjectDeleteView.as_view(), name='project_delete'),
    url(r'^project/(?P<pk>\d+)/history_list/$', views.ProjectHistoryListDatatablesView.as_view(), name='project_history_list'),
    url(r'^project/(?P<pk>\d+)/history_list/.json/$', views.ProjectHistoryListDatatablesView.as_view(), name='project_history_list.json', kwargs={"json": True}),
    url(r'^project/(?P<pk>\d+)/$', views.ProjectDetailView.as_view(), name='project_detail'),
)

urlpatterns += patterns('',
    url(r'^building/list/$', views.BuildingListDatatablesView.as_view(), name='building_list'),
    url(r'^building/list/.json/$', views.BuildingListDatatablesView.as_view(), name='building_list.json', kwargs={"json": True}),
    url(r'^building/list/.excel/$', views.BuildingListExcelView.as_view(), name='building_list.excel'),
    url(r'^building/create/$', views.BuildingFormView.as_view(), name='building_create', kwargs={"pk": 0}),
    url(r'^building/(?P<pk>\d+)/edit/$', views.BuildingFormView.as_view(), name='building_edit'),
    url(r'^building/(?P<pk>\d+)/delete/$', views.BuildingDeleteView.as_view(), name='building_delete'),
    url(r'^building/(?P<pk>\d+)/$', views.BuildingDetailView.as_view(), name='building_detail'),
)

urlpatterns += patterns('',
    url(r'^project/(?P<pk>\d+)/tracking/list/.json/$', views.ProjectTrackingListDatatablesView.as_view(), name='projecttracking_list', kwargs={"json": True}),
    url(r'^project/tracking/(?P<pk>\d+)/edit/$', views.ProjectTrackingFormView.as_view(), name='projecttracking_edit'),
    url(r'^project/tracking/create/$', views.ProjectTrackingFormView.as_view(), name='projecttracking_create', kwargs={"pk": 0}),
)

urlpatterns += patterns('',
    url(r'^building/(?P<pk>\d+)/housemodel/list/.json/$', views.HouseModelListDatatablesView.as_view(), name='housemodel_list', kwargs={"json": True}),
    url(r'^building/housemodel/(?P<pk>\d+)/edit/$', views.HouseModelFormView.as_view(), name='housemodel_edit'),
    url(r'^building/housemodel/create/$', views.HouseModelFormView.as_view(), name='housemodel_create', kwargs={"pk": 0}),
)