#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
from crispy_forms.bootstrap import InlineRadios
from django.core.urlresolvers import reverse
from django.forms import  HiddenInput
from django.utils import timezone
import os

from django import forms
from apps.account.models import User
from apps.common.admin.forms import CrispyModelForm, ModelDetail
from apps.customer.models import Customer, PartnerTracking, Partner
from apps.common.admin.datatables import DatatablesBuilder, DatatablesIdColumn, DatatablesTextColumn, \
    DatatablesColumnActionsRender, DatatablesActionsColumn, \
    DatatablesUserChoiceColumn, DatatablesDateColumn, DatatablesChoiceColumn
from utils import local_date_to_text


logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(__file__)))


class CustomerForm(CrispyModelForm):
    key_days_json = forms.CharField(required=False)
    # FIXME:
    #        在这里引入 '*_readonly' fields的原因是因为目前暂时没有一个简单的方案将一个field设置成readonly并且能够在html里
    #        正确显示。虽然可以直接将form的元素设置为 'disabled="disabled"'，但是这样的元素无法被form提交过来。所以在这里为
    #        了达到此效果，复制了需要readonly效果的fields，去实现'disabled="disabled"'来做界面的展示，而原来的fields在
    #        __init__()方法里将他们的widget换成HiddenInput()，从而使其保留初始的值以便form提交时可得到。
    partner_readonly = forms.ModelChoiceField(queryset=Partner.objects.none(),
                                              required=False)
    channel_type_readonly = forms.TypedChoiceField(choices=Customer.CHANNEL_TYPE_CHOICES,
                                                   required=False)

    def __init__(self, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        self.fields['key_days_json'].widget = forms.HiddenInput()
        self.fields['key_days_json'].initial = '[]'
        self.fields['owner'].queryset = User.staffs.active_objects().only("real_name").order_by('real_name')

        partner = self.initial.get('request').REQUEST.get('partner')
        if partner and not self.instance.id:
            self.fields['partner'].initial = partner
            self.fields['partner'].widget = forms.HiddenInput()
            self.fields['partner_readonly'].label = self.fields['partner'].label
            self.fields['partner_readonly'].initial = partner
            self.fields['partner_readonly'].queryset = Partner.active_objects.filter(pk=partner).only('name')
            self.fields['partner_readonly'].widget.attrs.update({'disabled': 'disabled'})

            self.fields['channel_type'].initial = Customer.CHANNEL_TYPE_PARTNER
            self.fields['channel_type'].widget = forms.HiddenInput()
            self.fields['channel_type_readonly'].label = self.fields['channel_type'].label
            self.fields['channel_type_readonly'].initial = Customer.CHANNEL_TYPE_PARTNER
            self.fields['channel_type_readonly'].widget.attrs.update({'disabled': 'disabled'})
            channel_type_index = self.helper['channel_type_readonly'].slice[0][0][0]
            self.helper[channel_type_index] = InlineRadios('channel_type_readonly')
        else:
            self.fields['partner'].queryset = Partner.active_objects.only('name')
            channel_type_index = self.helper['channel_type'].slice[0][0][0]
            self.helper[channel_type_index] = InlineRadios('channel_type')
            # XXX: must delete layout as well as field
            del self.fields['partner_readonly']
            del self.helper[self.helper['partner_readonly'].slice[0][0][0]]
            del self.fields['channel_type_readonly']
            del self.helper[self.helper['channel_type_readonly'].slice[0][0][0]]

    class Meta:
        model = Customer
        fields = ('name', 'phone', 'qq', 'email', 'wechat', 'channel_type', 'channel_type_readonly', 'partner',
                  'partner_readonly', 'owner', 'description', 'key_days_json')

    def clean_key_days_json(self):
        key_days_json = self.cleaned_data.get('key_days_json', "[]")
        if not key_days_json:
            return ""
        return key_days_json

    def clean(self):
        cleaned_data = super(CustomerForm, self).clean()
        if cleaned_data['channel_type'] == Customer.CHANNEL_TYPE_PARTNER and not cleaned_data['partner']:
            raise forms.ValidationError(u'渠道类型是合作伙伴, 必须填写合作伙伴信息')
        if cleaned_data['channel_type'] != Customer.CHANNEL_TYPE_PARTNER and cleaned_data['partner']:
            raise forms.ValidationError(u'渠道类型不是合作伙伴, 不允许填写合作伙伴信息')
        # qq, 电话号码, 微信号唯一性检查
        unique_fields = [('qq', 'qq'), ('phone', u'电话'), ('wechat', u'微信号'), ('email', u'电子邮件')]
        for (field_name, field_title) in unique_fields:
            field_value = cleaned_data[field_name]
            if field_value and Customer.active_objects.filter(**{field_name: field_value}).exclude(id=self.instance.id).count() > 0:
                raise forms.ValidationError(u'已经存在相同%s的客户' % field_title)
        return cleaned_data

    def save(self, commit=False):
        customer = super(CustomerForm, self).save(commit)
        if not hasattr(customer, "creator"):
            customer.creator = self.initial['request'].user
        customer.key_days = self.cleaned_data['key_days_json']
        customer.save()
        return customer


class PartnerForm(CrispyModelForm):
    key_days_json = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(PartnerForm, self).__init__(*args, **kwargs)
        self.fields['key_days_json'].widget = forms.HiddenInput()
        self.fields['key_days_json'].initial = '[]'
        self.fields['owner'].queryset = User.staffs.active_objects().only("real_name").order_by('real_name')

        type_index = self.helper['type'].slice[0][0][0]
        self.helper[type_index] = InlineRadios('type')

    def save(self, commit=False):
        partner = super(PartnerForm, self).save(commit)
        if not hasattr(partner, "creator"):
            partner.creator = self.initial['request'].user
        partner.key_days = self.cleaned_data['key_days_json']
        partner.save()
        return partner

    class Meta:
        model = Partner
        fields = ('name', 'contacts', 'phone', 'mobile', 'qq', 'wechat', 'email', 'type',
                  'owner', 'description', 'key_days_json')


class CustomerDatatablesBuilder(DatatablesBuilder):

    id = DatatablesIdColumn()

    name = DatatablesTextColumn(is_searchable=True,
                                access_check=True,
                                link_resolve=lambda request, model, field_name: (reverse('admin:customer:customer_detail',
                                                                                         kwargs={'pk': model.id}),
                                                                                 model.name))
    channel_type = DatatablesChoiceColumn(Customer.CHANNEL_TYPE_CHOICES,
                                          is_searchable=True)

    created = DatatablesDateColumn()

    owner = DatatablesUserChoiceColumn()

    class Meta:
        model = Customer


class PartnerDatatablesBuilder(DatatablesBuilder):

    id = DatatablesIdColumn()

    name = DatatablesTextColumn(is_searchable=True,
                                access_check=True,
                                link_resolve=lambda request, model, field_name: (reverse('admin:customer:partner_detail',
                                                                                         kwargs={'pk': model.id}),
                                                                                 model.name))

    contacts = DatatablesTextColumn(is_searchable=True)

    type = DatatablesChoiceColumn(Partner.PARTNER_TYPE_CHOICES,
                                  is_searchable=True)

    last_contact_date = DatatablesDateColumn(col_width="12%")

    created = DatatablesDateColumn()

    owner = DatatablesUserChoiceColumn(label=u'跟进人')

    class Meta:
        model = Partner


class PartnerTrackingForm(CrispyModelForm):

    def __init__(self, *args, **kwargs):
        super(PartnerTrackingForm, self).__init__(*args, **kwargs)
        self.fields['contact_date'].initial = local_date_to_text(timezone.now().date())
        self.fields['partner'].widget = HiddenInput()

        contact_method_index = self.helper['contact_method'].slice[0][0][0]
        self.helper[contact_method_index] = InlineRadios('contact_method')

    class Meta:
        model = PartnerTracking
        fields = ('contact_method', 'contact_date', 'description', 'question', 'solution', 'partner')

    def save(self, commit=False):
        partner_tracking = super(PartnerTrackingForm, self).save(commit)
        if not hasattr(partner_tracking, "creator"):
            partner_tracking.creator = self.initial['request'].user
        partner_tracking.save()
        return partner_tracking


class PartnerTrackingDatatablesBuilder(DatatablesBuilder):

    id = DatatablesIdColumn()

    contact_method = DatatablesTextColumn(col_width='10%')

    contact_date = DatatablesDateColumn()

    description = DatatablesTextColumn()

    question = DatatablesTextColumn()

    solution = DatatablesTextColumn()

    def actions_render(request, model, field_name):
        actions = [{'is_link': True, 'name': 'edit', 'text': u'编辑', 'icon': 'icon-edit', 'modal_show': True}]
        return DatatablesColumnActionsRender(actions=actions).render(request, model, field_name)

    _actions = DatatablesActionsColumn(render=actions_render)

    class Meta:
        model = PartnerTracking

class KeyDaysMixin(object):
    def get_key_days_display(self, model):
        try:
            key_days = json.loads(model.key_days)
        except:
            return ""
        if not key_days:
            return ""
        html = u'<table class="table table-striped table-bordered table-hover"><thead><tr><td>标题</td><td>日期</td><td>描述</td></thead><tbody>%s</tbody></table>'
        try:
            row = ""
            for item in key_days:
                row += u"<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (item.get('name', ''), item.get('key_day', ''), item.get('description', ''))
            return html % row
        except:
            return ""


class CustomerDetail(KeyDaysMixin, ModelDetail):

    class Meta:
        model = Customer
        excludes = ('is_active',)
        prefetch_fields = ('projects',)
        fields_order = CustomerForm.Meta.fields

    def get_partner_display(self, model):
        if not model.partner:
            return ''
        html = '<a href="#" data-url="%s">%s</a>'
        html = html % (reverse('admin:customer:partner_detail',
                               kwargs={'pk': model.partner_id}), unicode(model.partner))
        return html


class PartnerDetail(KeyDaysMixin, ModelDetail):

    class Meta:
        model = Partner
        excludes = ('is_active',)
        fields_order = PartnerForm.Meta.fields


class CustomerExcelForm(forms.ModelForm):
    _key_days = forms.CharField(label=u"个人重要日期")

    class Meta:
        model = Customer
        fields = ('name', 'phone', 'qq', 'email', 'wechat', 'channel_type', 'partner', 'owner',
                  'description', '_key_days')


class PartnerExcelForm(forms.ModelForm):
    _trackings = forms.CharField(label=u'沟通记录')

    _key_days = forms.CharField(label=u"个人重要日期")

    class Meta:
        model = Partner
        fields = ('name', 'contacts', 'phone', 'mobile', 'qq', 'wechat', 'email', 'type',
                  'owner', 'description', '_trackings', '_key_days')
