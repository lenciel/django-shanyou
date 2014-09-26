#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from django.core.urlresolvers import reverse
from django.utils.safestring import SafeBytes
import os
import json
from apps.customer.forms import CustomerDatatablesBuilder, CustomerForm, PartnerTrackingForm, PartnerForm, PartnerDatatablesBuilder, CustomerDetail, PartnerDetail, PartnerTrackingDatatablesBuilder, CustomerExcelForm, PartnerExcelForm
from apps.customer.models import Customer, Partner, PartnerTracking
from apps.common.admin.views import NavigationHomeMixin, ModelAwareMixin, DatatablesBuilderMixin,\
     AjaxDatatablesView, RequestAwareMixin, \
    ModelActiveView, ModelAccessibilityMixin, ModelDetailView, ModelAwareBaseMixin, AjaxFormView, ExcelExportView, \
    AdminRequiredMixin
from apps.project.forms import ProjectDatatablesBuilder
from apps.project.models import Project
from apps.project.views import ProjectListDatatablesView
from utils import local_date_to_text

HERE = os.path.dirname(__file__)
logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(HERE)) + '.' + os.path.basename(HERE))


HABIT_TEMPLATE = """* 是否抽烟:

* 是否饮酒:

* 兴趣爱好:

* 其他习惯:
"""


class CustomerListDatatablesView(NavigationHomeMixin, ModelAwareMixin, DatatablesBuilderMixin, AjaxDatatablesView):
    model = Customer
    datatables_builder_class = CustomerDatatablesBuilder
    queryset = Customer.objects.prefetch_related("owner")


class CustomerFormView(RequestAwareMixin, ModelAwareMixin, AjaxFormView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customer/admin/customer.form.inc.html'

    def get_initial(self):
        init = super(CustomerFormView, self).get_initial()
        if not self.object:
            init['owner'] = self.request.user
            init['description'] = HABIT_TEMPLATE
        return init

    def get_context_data(self, **kwargs):
        context = super(CustomerFormView, self).get_context_data(**kwargs)
        if self.object:
            key_days = self.object.key_days if self.object.key_days else "[]"
            context['key_days_json'] = SafeBytes(key_days.encode('utf-8'))
        return context


class CustomerDeleteView(ModelAccessibilityMixin, ModelActiveView):
    model = Customer

    def update(self, customer):
        if customer.projects.count() > 0:
            return u'存在与项目的关联，无法删除。'
        customer.delete()


class CustomerDetailView(ModelAccessibilityMixin, ModelAwareMixin, ModelDetailView):
    model_detail_class = CustomerDetail
    model = model_detail_class.Meta.model
    related_sources = [{"builder_class": ProjectDatatablesBuilder,
                       'datatable_list_name': 'admin:customer:customer_project_list',
                       'modal_class': Project,
                       'model_verbose_name': u'关联项目'}]


class CustomerProjectListDatatablesView(AjaxDatatablesView):
    datatables_builder_class = ProjectListDatatablesView.datatables_builder_class

    def get_queryset(self):
        return ProjectListDatatablesView.queryset.filter(customer_id=self.kwargs['pk'])


class CustomerListExcelView(AdminRequiredMixin, ExcelExportView):
    model = Customer
    queryset = Customer.objects.prefetch_related("owner", "partner")
    excel_file_name = u'客户.xls'
    model_form_class = CustomerExcelForm
    col_width = {'email': 6000, '_key_days': 8000, 'partner': 5000, 'wechat': 5000}

    def handle_related_field(self, model, field_value, field_name, field):
        if field_name == 'partner':
            field_value = model.partner.name if model.partner else ''
        else:
            raise NotImplementedError()
        return field_value

    def handle_unknown_field(self, model, field_name):
        if field_name == '_key_days':
            key_days = json.loads(model.key_days)[:5] if model.key_days else []
            field_value = '\n'.join(
                [u'%s, %s %s' % (item.get('name', ''), item.get('key_day', ''), item.get('description', '')) for item in key_days]
            )
        else:
            raise NotImplementedError()
        return field_value

##############################
#  partner
###############################


class PartnerListDatatablesView(NavigationHomeMixin, ModelAwareMixin, DatatablesBuilderMixin, AjaxDatatablesView):
    model = Partner
    queryset = Partner.objects.prefetch_related("owner")
    datatables_builder_class = PartnerDatatablesBuilder


class PartnerFormView(CustomerFormView):
    model = Partner
    form_class = PartnerForm


class PartnerDeleteView(ModelAccessibilityMixin, ModelActiveView):
    model = Partner

    def update(self, partner):
        if partner.customers.count() > 0:
            return u'存在与客户的关联，无法删除。'
        partner.delete()


class PartnerDetailView(ModelAccessibilityMixin, ModelAwareMixin, ModelDetailView):
    model_detail_class = PartnerDetail
    model = model_detail_class.Meta.model

    def get_related_sources(self, master_model):
        return [{"builder_class": PartnerTrackingDatatablesBuilder,
                 'datatable_list_name': 'admin:customer:partnertracking_list',
                 'modal_class': PartnerTracking,
                 'create_url': reverse('admin:customer:partnertracking_create'),
                 'modal_show': True},
                {"builder_class": CustomerDatatablesBuilder,
                 'datatable_list_name': 'admin:customer:partner_customer_list',
                 'modal_class': Customer,
                 'model_verbose_name': u'关联客户',
                 'modal_show': False}
                ]


class PartnerCustomerListDatatablesView(AjaxDatatablesView):
    datatables_builder_class = CustomerListDatatablesView.datatables_builder_class

    def get_queryset(self):
        return CustomerListDatatablesView.queryset.filter(partner_id=self.kwargs['pk'])


class PartnerListExcelView(AdminRequiredMixin, ExcelExportView):
    model = Partner
    queryset = Partner.objects.prefetch_related("owner")
    excel_file_name = u'合作伙伴.xls'
    model_form_class = PartnerExcelForm
    col_width = {'email': 6000, '_key_days': 8000, 'wechat': 5000, 'description': 10000, "_trackings": 15000}

    def handle_unknown_field(self, model, field_name):
        if field_name == '_trackings':
            field_value = '\n--------------------------------\n'. \
                join([u"%s %s\n问题:\n%s\n解决办法:\n%s" % \
                      (local_date_to_text(obj.updated), obj.get_contact_method_display(), obj.question, obj.solution)
                      for obj in model.trackings.all()[:5]])
        elif field_name == '_key_days':
            key_days = json.loads(model.key_days)[:5] if model.key_days else []
            field_value = '\n'.join(
                [u'%s, %s %s' % (item.get('name', ''), item.get('key_day', ''), item.get('description', '')) for item in key_days]
            )
        else:
            raise NotImplementedError()
        return field_value

##############################
#  partner tracking
###############################


class PartnerTrackingListDatatablesView(AjaxDatatablesView):
    datatables_builder_class = PartnerTrackingDatatablesBuilder

    def get_queryset(self):
        return PartnerTracking.objects.filter(partner_id=self.kwargs['pk'])


class PartnerTrackingFormView(RequestAwareMixin, ModelAwareBaseMixin, AjaxFormView):
    model = PartnerTracking
    form_class = PartnerTrackingForm

    def get_initial(self):
        init = super(PartnerTrackingFormView, self).get_initial()
        if not self.object:
            init['partner'] = Partner.objects.only('id').get(id=self.request.REQUEST['partner'])
        return init

