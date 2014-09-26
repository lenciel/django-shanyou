#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from apps.common.admin.views import ModelAwareMixin, AjaxUpdateView, NavigationHomeMixin, AjaxDatatablesView, DatatablesBuilderMixin, AjaxListView, RequestAwareMixin, AjaxCreateView, ModelActiveView, AjaxSimpleUpdateView, AjaxFormView
from apps.foundation.forms import ImageForm, ClientAppDatatablesBuilder, ClientAppForm
from apps.foundation.models import ClientApp

logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(__file__)))


IMAGE_MIN_WIDTH = 0
IMAGE_MIN_HEIGHT = 0

@csrf_exempt
def upload_image_view(request):
    form = ImageForm(request.POST, request.FILES)
    status = 400
    if form.is_valid():
        obj = form.save(commit=False)
        if obj.width < IMAGE_MIN_WIDTH or obj.height < IMAGE_MIN_HEIGHT:
            state = u'图片尺寸至少%dx%d' % (IMAGE_MIN_WIDTH, IMAGE_MIN_HEIGHT)
        else:
            state = 'SUCCESS'
            obj.save()
        status = 200
        resp = "{'original':'%s','url':'%s','title':'%s','state':'%s'}" % \
               ("", obj.image_file.url, "", state)
        return HttpResponse(content=resp, status=status)

    return HttpResponse(status=status)


class ClientAppListDatatablesView(NavigationHomeMixin, ModelAwareMixin, DatatablesBuilderMixin, AjaxDatatablesView):
    model = ClientApp
    datatables_builder_class = ClientAppDatatablesBuilder
    queryset = ClientApp.objects.active_queryset().order_by('-updated')


class ClientAppFormView(RequestAwareMixin, ModelAwareMixin, AjaxFormView):
    model = ClientApp
    form_class = ClientAppForm
    template_name = 'foundation/admin/clientapp.form.inc.html'


class ClientAppDeleteView(AjaxSimpleUpdateView):
    model = ClientApp

    def update(self, obj):
        obj.delete()
        return ""


def download_android_view(request):
    url = ClientApp.objects.get_latest_android_app().download_url()
    return HttpResponseRedirect(url, content_type="application/vnd.android.package-archive")