#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from apps.account import views


urlpatterns = patterns('',
    url(r'^login/$', views.login_view, name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),

    url(r'^user/list/$', views.UserListDatatablesView.as_view(), name='user_list'),
    url(r'^user/list/.json/$', views.UserListDatatablesView.as_view(), name='user_list.json', kwargs={'json': True}),
    url(r'^user/create/$', views.UserFormView.as_view(), name='user_create', kwargs={'pk': 0}),
    url(r'^user/(?P<pk>\d+)/edit/$', views.UserFormView.as_view(), name='user_edit'),
    url(r'^user/(?P<pk>\d+)/unlock/$', views.UserLockView.as_view(), name='user_lock'),
    url(r'^user/(?P<pk>\d+)/lock/$', views.UserUnlockView.as_view(), name='user_unlock'),
    url(r'^user/(?P<pk>\d+)/change_password/$', views.UserChangePasswordView.as_view(), name='change_password'),
)

urlpatterns += patterns('',
    url(r'^group/list/$', views.GroupListDatatablesView.as_view(), name='group_list'),
    url(r'^group/list/.json/$', views.GroupListDatatablesView.as_view(), name='group_list.json', kwargs={"json": True}),
    url(r'^group/create/$', views.GroupFormView.as_view(), name='group_create', kwargs={'pk': 0}),
    url(r'^group/(?P<pk>\d+)/edit/$', views.GroupFormView.as_view(), name='group_edit'),
    url(r'^group/(?P<pk>\d+)/delete/$', views.GroupDeleteView.as_view(), name='group_delete'),
)

urlpatterns += patterns('',
    url(r'^department/list/$', views.DepartmentListDatatablesView.as_view(), name='department_list'),
    url(r'^department/list/.json/$', views.DepartmentListDatatablesView.as_view(), name='department_list.json', kwargs={"json": True}),
    url(r'^department/create/$', views.DepartmentFormView.as_view(), name='department_create', kwargs={'pk': 0}),
    url(r'^department/(?P<pk>\d+)/edit/$', views.DepartmentFormView.as_view(), name='department_edit'),
    url(r'^department/(?P<pk>\d+)/delete/$', views.DepartmentDeleteView.as_view(), name='department_delete'),
)

urlpatterns += patterns('',
    url(r'^user/password_reset/',  views.UserResetPasswordView.as_view(),
        # We can't use reverse() because django failed to lookup the url name which is defined in same list also.
        # At this moment, this url name is not available to global url cache.
        {'post_reset_redirect': '/admin/account/user/password_reset_done/',
        'email_template_name': 'account/password_reset_email.html',
        'subject_template_name': 'account/password_reset_subject.txt'},
        name='password_reset'),
    url(r'^user/password_reset_confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'template_name': 'account/password_reset_confirm.html',
         'post_reset_redirect': '/admin/account/user/password_reset_complete/'},
        name='password_reset_confirm'),
    url(r'^user/password_reset_complete/', 'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'account/password_reset_complete.html'},
        name='password_reset_complete'),
)
