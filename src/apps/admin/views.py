#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import subprocess
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.http import HttpResponse
from django.views.generic import TemplateView

from os import environ
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.decorators import login_required
import os
from apps.common.admin.views import AdminRequiredMixin

HERE = os.path.dirname(__file__)
logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(HERE)) + '.' + os.path.basename(HERE))


def build_menu(request):
    SUBMENU_ACCOUNT = [
        # ('用户组', reverse('admin:account:group_list'), lambda request: request.user.is_admin()),
        ('部门', reverse('admin:account:department_list'), lambda request: request.user.is_superuser),
        ('账号', reverse('admin:account:user_list'), lambda request: request.user.is_superuser),
        ('Excel导出', reverse('admin:excel_export_center'), lambda request: request.user.is_superuser),
    ]

    SUBMENU_CATALOG = [
        # productcategory and brand both use the 'change_productcategory' permission
        ('品牌', reverse('admin:catalog:brand_list'), lambda request: request.user.is_superuser or \
                                                                     request.user.has_perm('catalog.change_productcategory')),
        ('类型', reverse('admin:catalog:productcategory_list'), lambda request: request.user.is_superuser or \
                                                                      request.user.has_perm('catalog.change_productcategory')),
        #('产品', reverse('admin:catalog:product_list'), None),
    ]

    #SUBMENU_FOUNDATION = [
    #    ('客户端APP', reverse('admin:foundation:clientapp_list'), None),
    #]

    MENU = (
        {'menu': '系统信息', 'url': reverse('admin:dashboard'), 'icon': 'icon-dashboard', 'color': 'blue', 'submenu': []},
        {'menu': '项目', 'url': reverse('admin:project:project_list'), 'icon': 'icon-road', 'color': 'green','submenu': []},
        {'menu': '客户', 'url': reverse('admin:customer:customer_list'), 'icon': 'icon-user', 'color': 'pink','submenu': []},
        {'menu': '合作伙伴', 'url': reverse('admin:customer:partner_list'), 'icon': 'icon-suitcase', 'color': 'blue','submenu': []},
        {'menu': '楼盘', 'url': reverse('admin:project:building_list'), 'icon': 'icon-hospital', 'color': 'green','submenu': []},
        {'menu': '产品', 'url': '', 'icon': 'icon-barcode', 'color': 'pink', 'submenu': SUBMENU_CATALOG},
        {'menu': '系统配置', 'url': '', 'icon': ' icon-cogs', 'color': 'blue', 'submenu': SUBMENU_ACCOUNT},
    )
    menus = []
    for item in MENU:
        has_permission = False
        menu = {"name": item['menu'], "url": item['url'], "icon": item['icon'], "color": item['color'], "submenus": []}
        for subitem in item['submenu']:
            if subitem[2] is None or (subitem[2] and subitem[2](request)):
                has_permission = True
                menu['submenus'].append({"name": subitem[0], "url": subitem[1]})
        if has_permission or menu['url']:
            menus.append(menu)
    # remove menu with empty submenu
    return [menu for menu in menus if menu['url'] or menu['submenus']]


def home(request):
    """
    重定向到login页面
    """
    site_name = settings.SITE_NAME
    if request.user.is_authenticated():
        if not request.user.is_staff:
            return redirect(reverse('website:customer:customer_home'))
        menus = build_menu(request)
        return render_to_response('admin/home.html',
                                  locals(),
                                  context_instance=RequestContext(request))

    # 如果没有登陆，返回默认的主页
    return redirect(reverse('admin:account:login'))


@login_required()
def dashboard(request):
    site_name = settings.SITE_NAME
    return render_to_response('admin/dashboard.inc.html',
                              locals(),
                              context_instance=RequestContext(request))


@login_required()
def system(request):
    try:
        env_settings = environ['DJANGO_SETTINGS_MODULE']
    except KeyError:
        env_settings = "not define in env"

    # get which tag is using in current branch
    #cmd = 'cd %s && git describe --abbrev=0 --tags' % settings.SITE_ROOT
    cmd = 'cd %s && git rev-list --date-order -n 1 --format=%%d HEAD' % settings.SITE_ROOT
    git_tag = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)

    active_settings = settings.SETTINGS_MODULE

    return render_to_response('admin/system.inc.html',
                              locals(),
                              context_instance=RequestContext(request))

@login_required()
def loaddata(request, filename):
    if not request.user.is_superuser:
        raise PermissionDenied
    call_command("loaddata", filename, settings=settings.SETTINGS_MODULE, traceback=True, verbosity=0)
    return HttpResponse(content='load data %s success' % filename)


@login_required()
def initdata(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    call_command("loaddata", "initial_data.json", settings=settings.SETTINGS_MODULE, traceback=True, verbosity=0)
    return HttpResponse(content='load data initial_data.json success')


class ExcelCenterView(AdminRequiredMixin, TemplateView):
    template_name = "admin/excel.center.inc.html"