#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
from django.core.urlresolvers import reverse
from django.utils.safestring import SafeString
import os
from apps.catalog.models import BrandToProductCategory
from apps.project.forms import ProjectForm, ProjectDatatablesBuilder, BuildingForm, BuildingDatatablesBuilder,\
    ProjectHistoryDatatablesBuilder, ProjectTrackingForm, ProjectDetail, BuildingDetail, ProjectTrackingDatatablesBuilder, HouseModelDatatablesBuilder, HouseModelForm, \
    BuildingExcelForm, ProjectExcelForm
from apps.project.models import Project, Building, ProjectHistory, ProjectTracking, HouseModel
from apps.common.admin.views import NavigationHomeMixin, ModelAwareMixin, DatatablesBuilderMixin, AjaxListView,\
    AjaxDatatablesView, RequestAwareMixin, AjaxSimpleUpdateView, ModelActiveView,\
    ModelAccessibilityMixin, ModelDetailView, ModelAwareBaseMixin, AjaxFormView, ExcelExportView, AdminRequiredMixin
from utils import local_date_to_text

HERE = os.path.dirname(__file__)
logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(HERE)) + '.' + os.path.basename(HERE))

################################
#           project
################################


class ProjectListDatatablesView(NavigationHomeMixin, ModelAwareMixin, DatatablesBuilderMixin, AjaxDatatablesView):
    model = Project
    datatables_builder_class = ProjectDatatablesBuilder
    queryset = Project.active_objects.select_related("customer__owner", "building")


class ProjectFormView(RequestAwareMixin, ModelAwareBaseMixin, AjaxFormView):
    form_class = ProjectForm
    model = Project
    template_name = 'project/admin/project.form.inc.html'

    def get_context_data(self, **kwargs):
        context = super(ProjectFormView, self).get_context_data(**kwargs)
        context['categories'] = SafeString(json.dumps(BrandToProductCategory.objects.group_by_category()))
        return context


class ProjectDeleteView(ModelAccessibilityMixin, AjaxSimpleUpdateView):
    model = Project

    def update(self, project):
        project.delete()


class ProjectDetailView(ModelAccessibilityMixin, ModelAwareMixin, ModelDetailView):
    model_detail_class = ProjectDetail
    model = model_detail_class.Meta.model

    def get_related_sources(self, master_model):
        return [{"builder_class": ProjectTrackingDatatablesBuilder,
                 'datatable_list_name': 'admin:project:projecttracking_list',
                 'modal_class': ProjectTracking,
                 'create_url': reverse('admin:project:projecttracking_create'),
                 'modal_show': True}]


class ProjectListExcelView(AdminRequiredMixin, ExcelExportView):
    model = Project
    queryset = Project.active_objects.select_related("building", "customer", "designer", "interesting_brand_categories")
    excel_file_name = u'项目.xls'
    model_form_class = ProjectExcelForm
    col_width = {"building": 10000, "interesting_brand_categories": 5000, "description": 5000, "_trackings": 15000, "_histories": 10000}

    def handle_related_field(self, model, field_value, field_name, field):
        if field_name == 'building':
            field_value = model.building.full_name
        elif field_name == 'customer':
            field_value = model.customer.name
        elif field_name == 'designer':
            field_value = model.designer.get_full_name() if model.designer else ""
        elif field_name == 'interesting_brand_categories':
            categories = [category.full_name for category in model.interesting_brand_categories.all()]
            field_value = '\n'.join(categories)
        else:
            raise NotImplementedError()
        return field_value

    def handle_unknown_field(self, model, field_name):
        if field_name == '_trackings':
            field_value = '\n--------------------------------\n'.\
                join([u"%s %s\n问题:\n%s\n解决办法:\n%s" % \
                      (local_date_to_text(obj.updated), obj.get_contact_method_display(), obj.question, obj.solution)
                      for obj in model.trackings.all()[:5]])
        else:
            raise NotImplementedError()
        return field_value

##############################
#  Project tracking
###############################

class ProjectTrackingListDatatablesView(AjaxDatatablesView):
    datatables_builder_class = ProjectTrackingDatatablesBuilder

    def get_queryset(self):
        return ProjectTracking.objects.filter(project_id=self.kwargs['pk'])


class ProjectTrackingFormView(RequestAwareMixin, ModelAwareBaseMixin, AjaxFormView):
    model = ProjectTracking
    form_class = ProjectTrackingForm

    def get_initial(self):
        init = super(ProjectTrackingFormView, self).get_initial()
        if not self.object:
            init['project'] = Project.objects.only('id').get(id=self.request.REQUEST['project'])
        return init


################################
#           Project history
################################

class ProjectHistoryListDatatablesView(ModelAwareMixin, DatatablesBuilderMixin, AjaxDatatablesView):
    model = ProjectHistory
    datatables_builder_class = ProjectHistoryDatatablesBuilder
    model_name = "project"

    def get_datatables_list_url(self):
        pk = self.kwargs.get('pk')
        return reverse('admin:project:project_history_list.json', kwargs={'pk': pk})

    def get_context_data(self, **kwargs):
        # XXX: a workaround to let ModelAwareMixin not handle "create_url"
        context = super(ProjectHistoryListDatatablesView, self).get_context_data(**kwargs)
        context['create_url'] = ""
        return context

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        return self.model.objects.select_related("building").filter(project=pk)


################################
#           building
################################


class BuildingListDatatablesView(NavigationHomeMixin, ModelAwareMixin, DatatablesBuilderMixin, AjaxDatatablesView):
    model = Building
    queryset = Building.active_objects.prefetch_related("creator")
    datatables_builder_class = BuildingDatatablesBuilder


class BuildingFormView(RequestAwareMixin, ModelAwareMixin, AjaxFormView):
    model = Building
    form_class = BuildingForm
    template_name = 'project/admin/building.form.inc.html'


class BuildingDeleteView(ModelActiveView):
    model = Building

    def update(self, building):
        if building.projects.count() > 0:
            return u'存在与项目的关联，无法删除。'
        building.delete()


class BuildingDetailView(ModelAwareMixin, ModelDetailView):
    # building has no modal access checking
    model_detail_class = BuildingDetail
    model = model_detail_class.Meta.model

    def get_related_sources(self, master_model):
        return [{"builder_class": HouseModelDatatablesBuilder,
                 'datatable_list_name': 'admin:project:housemodel_list',
                 'modal_class': HouseModel,
                 'create_url': reverse('admin:project:housemodel_create'),
                 'modal_show': True}]


class BuildingListExcelView(AdminRequiredMixin, ExcelExportView):
    model = Building
    queryset = Building.active_objects.prefetch_related("creator", "models")
    excel_file_name = u'楼盘.xls'
    model_form_class = BuildingExcelForm
    col_width = {"description": 5000, "address": 5000, "developer": 5000, "property_management": 5000, "housemodels": 10000}

    def handle_unknown_field(self, model, field_name):
        if field_name == 'housemodels':
            res = [u"%s %s(平方米) %s" % (housemodel.model, housemodel.area, housemodel.description)  for housemodel in model.models.all()]
            return "\n".join(res)
        raise NotImplementedError()


################################
#          house model
################################

class HouseModelListDatatablesView(AjaxDatatablesView):
    datatables_builder_class = HouseModelDatatablesBuilder

    def get_queryset(self):
        return HouseModel.objects.filter(building_id=self.kwargs['pk'])


class HouseModelFormView(RequestAwareMixin, ModelAwareBaseMixin, AjaxFormView):
    model = HouseModel
    form_class = HouseModelForm

    def get_initial(self):
        init = super(HouseModelFormView, self).get_initial()
        if not self.object:
            init['building'] = Building.objects.only('id').get(id=self.request.REQUEST['building'])
        return init