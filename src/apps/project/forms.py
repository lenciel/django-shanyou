#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from crispy_forms.bootstrap import FieldWithButtons, StrictButton, InlineRadios, InlineCheckboxes
from django.core.urlresolvers import reverse
from django.forms import HiddenInput, Select
from django.utils import timezone
import os

from django import forms
from apps.account.models import User
from apps.catalog.models import BrandToProductCategory
from apps.common.admin.forms import  CrispyModelForm, ModelDetail
from apps.customer.models import Customer
from apps.common.admin.datatables import DatatablesBuilder, DatatablesIdColumn, DatatablesTextColumn, \
    DatatablesChoiceColumn, DatatablesUserChoiceColumn, DatatablesColumnActionsRender, DatatablesActionsColumn, DatatablesDateTimeColumn, DatatablesDateColumn
from apps.project.models import Building, Project, ProjectHistory, ProjectTracking, HouseModel
from utils import local_date_to_text


logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(__file__)))


class ProjectForm(CrispyModelForm):
    class BrandCategoryMultipleChoiceField(forms.ModelMultipleChoiceField):
        def label_from_instance(self, obj):
            return unicode(obj.brand)

    # FIXME:
    #        在这里引入 '*_readonly' fields的原因是因为目前暂时没有一个简单的方案将一个field设置成readonly并且能够在html里
    #        正确显示。虽然可以直接将form的元素设置为 'disabled="disabled"'，但是这样的元素无法被form提交过来。所以在这里为
    #        了达到此效果，复制了需要readonly效果的fields，去实现'disabled="disabled"'来做界面的展示，而原来的fields在
    #        __init__()方法里将他们的widget换成HiddenInput()，从而使其保留初始的值以便form提交时可得到。
    customer_readonly = forms.ModelChoiceField(queryset=Customer.objects.none(),
                                               required=False)

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.fields['building'].widget.attrs['data-placeholder'] = u"选择楼盘"
        self.fields['building'].queryset = Building.active_objects.only("full_name")
        self.fields['designer'].queryset = User.staffs.active_objects().only('real_name')

        self.fields['interesting_brand_categories'] = self.BrandCategoryMultipleChoiceField(label=u'感兴趣品牌类型',
                                                                                            queryset=BrandToProductCategory.objects.select_related("brand").only('brand__name'))
        interesting_brand_categories_index = self.helper['interesting_brand_categories'].slice[0][0][0]
        self.helper[interesting_brand_categories_index] = InlineCheckboxes('interesting_brand_categories')
        self.fields['interesting_brand_categories'].help_text = u''

        if not self.instance.id or not self.instance.willing == Project.WILLING_S_SIGNED:
            self.fields['contract_status'].widget = forms.HiddenInput()
            self.fields['contract_status'].initial = Project.CONTRACT_STATUS_NONE
        # a script to open the screen of add building
        building_add_script = "window.location.hash='%s#main-content'" % reverse('admin:project:building_create')

        building_index = self.helper['building'].slice[0][0][0]
        self.helper[building_index] = FieldWithButtons('building',
            StrictButton(u"添加楼盘", css_class='btn-purple btn-sm', id='id_building_add', onclick=building_add_script))

        willing_index = self.helper['willing'].slice[0][0][0]
        self.helper[willing_index] = InlineRadios('willing')

        contract_status_index = self.helper['contract_status'].slice[0][0][0]
        self.helper[contract_status_index] = InlineRadios('contract_status')

        if self.initial['request'].method == 'GET':
            customer = self.initial.get('request').GET.get('customer')
            if customer and not self.instance.id:
                self.fields['customer'].initial = customer
                self.fields['customer'].widget = forms.HiddenInput()
                self.fields['customer_readonly'].label = self.fields['customer'].label
                self.fields['customer_readonly'].initial = customer
                self.fields['customer_readonly'].queryset = Customer.active_objects.filter(pk=customer).only('name')
                self.fields['customer_readonly'].widget.attrs.update({'disabled': 'disabled'})
            else:
                self.fields['customer'].queryset = Customer.active_objects.only('name').\
                    filter(owner__in=self.initial['request'].user.accessible_user_ids())
                del self.fields['customer_readonly']
                # XXX: must delete layout as well as field
                del self.helper[self.helper['customer_readonly'].slice[0][0][0]]


    def clean(self):
        cleaned_data = super(ProjectForm, self).clean()
        if cleaned_data['willing'] != Project.WILLING_S_SIGNED and cleaned_data['contract_status'] > Project.CONTRACT_STATUS_NONE :
            raise forms.ValidationError(u'不是签约客户, 不能修改合同状态')
        return cleaned_data

    class Meta:
        model = Project
        fields = ('building', 'house_number', 'contacts', 'phone', 'customer', 'customer_readonly', 'willing', 'contract_status', 'designer',
                  'interesting_brand_categories', 'description')

    def clean_contract_status(self):
        self.old_contract_status = self.instance.contract_status
        return self.cleaned_data['contract_status']

    def save(self, commit=False):
        project = super(ProjectForm, self).save(commit)
        status_changed = project.contract_status != self.old_contract_status or not project.id
        if not hasattr(project, "creator"):
            project.creator = self.initial['request'].user
            project.owner = project.creator
        project.save()

        if status_changed:
            history = ProjectHistory(project=project,
                                     status=project.contract_status,
                                     creator=self.initial['request'].user, )
            history.save()

        return project


class ProjectDatatablesBuilder(DatatablesBuilder):
    id = DatatablesIdColumn()

    building = DatatablesTextColumn(is_searchable=True,
                                    access_check=True,
                                    search_expr="building__name__icontains",
                                    link_resolve=lambda request, model, field_name: (reverse('admin:project:project_detail',
                                                                                             kwargs={'pk': model.id}),
                                                                                     unicode(model.building.name)))

    city = DatatablesTextColumn(label=u'城市',
                                is_searchable=True,
                                col_width='5%',
                                search_expr="building__city__icontains",
                                render=(lambda request, model, field_name: unicode(model.building.city)))

    house_number = DatatablesTextColumn(is_searchable=True)

    contacts = DatatablesTextColumn(is_searchable=True)

    contract_status = DatatablesChoiceColumn(Project.CONTRACT_STATUS_CHOICES,
                                             is_searchable=True,
                                             col_width="5%")

    willing = DatatablesChoiceColumn(Project.WILLING_CHOICES,
                                     is_searchable=True,
                                     col_width="5%")

    # 项目所属客户的owner
    customer__owner = DatatablesUserChoiceColumn(label=u'跟进人',
                                                 render=(lambda request, model, field_name: model.customer.owner.real_name))

    created = DatatablesDateColumn()

    class Meta:
        model = Project


class ProjectDetail(ModelDetail):

    class Meta:
        model = Project
        excludes = ('is_active',)
        fields_order = ProjectForm.Meta.fields
        prefetch_fields = ('customer', 'building')

    def get_interesting_brand_categories_display(self, model):
        html = ""
        for item in model.interesting_brand_categories.only('full_name').all():
            html += '<span class="label label-xlg label-purple arrowed-right">%s</span>' % unicode(item)
        return html

    def get_customer_display(self, model):
        html = '<a href="#" data-url="%s">%s</a>'
        html = html % (reverse('admin:customer:customer_detail',
                               kwargs={'pk': model.customer_id}), unicode(model.customer))
        return html

    def get_building_display(self, model):
        html = '<a href="#" data-url="%s">%s</a>'
        html = html % (reverse('admin:project:building_detail',
                               kwargs={'pk': model.building_id}), unicode(model.building))
        return html


class ProjectExcelForm(forms.ModelForm):
    _trackings = forms.CharField(label=u'沟通记录')

    class Meta:
        model = Project
        fields = ('building', 'house_number', 'contacts', 'phone', 'customer', 'willing', 'contract_status', 'designer',
                  'interesting_brand_categories', 'description',) + ('_trackings',)

##########################
#  history
##########################

class ProjectHistoryDatatablesBuilder(DatatablesBuilder):
    id = DatatablesIdColumn()

    project = DatatablesTextColumn(render=lambda request, model, field_name: unicode(model.project),)

    status = DatatablesChoiceColumn(Project.CONTRACT_STATUS_CHOICES)

    creator = DatatablesTextColumn()

    created = DatatablesDateTimeColumn()

    class Meta:
        model = ProjectHistory

##########################
#  Tracking
##########################

class ProjectTrackingForm(CrispyModelForm):

    def __init__(self, *args, **kwargs):
        super(ProjectTrackingForm, self).__init__(*args, **kwargs)
        self.fields['contact_date'].initial = local_date_to_text(timezone.now().date())
        self.fields['project'].widget = HiddenInput()
        contact_method_index = self.helper['contact_method'].slice[0][0][0]
        self.helper[contact_method_index] = InlineRadios('contact_method')

    class Meta:
        model = ProjectTracking
        fields = ('contact_method', 'contact_date', 'description', 'question', 'solution', 'project')

    def save(self, commit=False):
        project_tracking = super(ProjectTrackingForm, self).save(commit)
        if not hasattr(project_tracking, "creator"):
            project_tracking.creator = self.initial['request'].user
        project_tracking.save()
        return project_tracking


class ProjectTrackingDatatablesBuilder(DatatablesBuilder):

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
        model = ProjectTracking

##########################
#  building
##########################

class BuildingForm(CrispyModelForm):

    def __init__(self, *args, **kwargs):
        super(BuildingForm, self).__init__(*args, **kwargs)
        self.fields['province'].widget = Select()
        self.fields['city'].widget = Select()
        self.fields['district'].widget = Select()

    class Meta:
        model = Building
        fields = ('province',
                  'city',
                  'district',
                  'address',
                  'name',
                  'developer',
                  'property_management',
                  'avg_price_min',
                  'avg_price_max',
                  'total_price_min',
                  'total_price_max',
                  'amount',
                  'description',)

    def save(self, commit=False):
        building = super(BuildingForm, self).save(commit)
        if not hasattr(building, "creator"):
            building.creator = self.initial['request'].user
            building.owner = self.initial['request'].user
        building.save()
        return building


class BuildingDatatablesBuilder(DatatablesBuilder):
    id = DatatablesIdColumn()

    name = DatatablesTextColumn(is_searchable=True,
                                link_resolve=lambda request, model, field_name: (reverse('admin:project:building_detail',
                                                                                         kwargs={'pk': model.id}),
                                                                                 model.name))

    city = DatatablesTextColumn(is_searchable=True,
                                col_width='5%')

    developer = DatatablesTextColumn(is_searchable=True)

    creator = DatatablesUserChoiceColumn()

    avg_price_min = DatatablesTextColumn(label=u'最低单价',
                                         is_searchable=True,
                                         search_expr='avg_price_min__gte')

    avg_price_max = DatatablesTextColumn(label=u'最高单价',
                                         is_searchable=True,
                                         search_expr='avg_price_max__lte')

    total_price_min = DatatablesTextColumn(label=u'最低总价',
                                           is_searchable=True,
                                           search_expr='total_price_min__gte')

    total_price_max = DatatablesTextColumn(label=u'最高总价',
                                           is_searchable=True,
                                           search_expr='total_price_max__lte')

    def actions_render(request, model, field_name):
        actions = [{'is_link': True, 'name': 'edit', 'text': u'编辑', 'icon': 'icon-edit'}]
        return DatatablesColumnActionsRender(actions=actions).render(request, model, field_name)

    _actions = DatatablesActionsColumn(render=actions_render)

    class Meta:
        model = Building


class BuildingDetail(ModelDetail):

    class Meta:
        model = Building
        excludes = ('is_active', 'owner')
        fields_order = BuildingForm.Meta.fields


class BuildingExcelForm(forms.ModelForm):
    housemodels = forms.CharField(label=u'户型')

    class Meta:
        model = Building
        fields = BuildingForm.Meta.fields + ("housemodels",)


class HouseModelForm(CrispyModelForm):

    def __init__(self, *args, **kwargs):
        super(HouseModelForm, self).__init__(*args, **kwargs)
        self.fields['building'].widget = HiddenInput()

    class Meta:
        model = HouseModel
        fields = ('model', 'area', 'description', 'building')


class HouseModelDatatablesBuilder(DatatablesBuilder):
    id = DatatablesIdColumn()

    model = DatatablesTextColumn()

    area = DatatablesTextColumn()

    description = DatatablesTextColumn()

    def actions_render(request, model, field_name):
        actions = [{'is_link': True, 'name': 'edit', 'text': u'编辑', 'icon': 'icon-edit', 'modal_show': True}]
        return DatatablesColumnActionsRender(actions=actions).render(request, model, field_name)

    _actions = DatatablesActionsColumn(render=actions_render)

    class Meta:
        model = HouseModel
