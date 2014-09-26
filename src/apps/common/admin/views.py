#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import datetime
import types
from crispy_forms.helper import FormHelper
import os
import sys
import time
from types import FunctionType, StringType
import django
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db.models import FieldDoesNotExist
from django.forms import CharField, ChoiceField
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.datastructures import SortedDict
from django.utils.safestring import SafeString
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from xlwt import Workbook, easyxf
from apps.common import exceptions
from .forms import ModelDetail
import utils

HERE = os.path.dirname(__file__)
logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(HERE)) + '.' + os.path.basename(HERE))


class ActionUrlBuilderMixin(object):
    def get_action_url(self, model, action):
        namespace = getattr(self, 'app_label', None)
        if not namespace:
            namespace = model._meta.app_label
        namespace = "admin:" + namespace
        model_name = getattr(self, 'model_name', None)
        if not model_name:
            model_name = model._meta.object_name.lower()
        return '%s:%s_%s' % (namespace, model_name, action)


class AjaxLoginRequiredMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise exceptions.AjaxAuthRequired()
        return super(AjaxLoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class AdminRequiredMixin(object):
    """
    Mixin allows you to require a user with `is_superuser` set to True.
    """
    def dispatch(self, request, *args, **kwargs):
        # If the user is a supper user,
        if not request.user.is_superuser:
            raise exceptions.AjaxPermissionDeny()
        return super(AdminRequiredMixin, self).dispatch(request, *args, **kwargs)


class StaffRequiredMixin(object):
    """
    Mixin allows you to require a user with `is_staff` set to True.
    """
    def dispatch(self, request, *args, **kwargs):
        # If the user is a staff user,
        if not request.user.is_staff:
            raise exceptions.AjaxPermissionDeny()
        return super(StaffRequiredMixin, self).dispatch(request, *args, **kwargs)


class PermissionRequiredMixin(object):
    """
View mixin which verifies that the logged in user has the specified
permission.

Class Settings
`permission_required` - the permission to check for.

get from https://github.com/brack3t/django-braces/blob/master/braces/views.py
"""
    permission_required = None # Default required perms to none

    def dispatch(self, request, *args, **kwargs):
        # Make sure that the permission_required attribute is set on the
        # view, or raise a configuration error.
        if self.permission_required is None:
            raise ImproperlyConfigured(
                "'PermissionRequiredMixin' requires "
                "'permission_required' attribute to be set.")

        if not request.user.is_staff:
            raise exceptions.AjaxPermissionDeny()

        # Check to see if the request's user has the required permission.
        has_permission = request.user.is_superuser or request.user.has_perm(self.permission_required)
        # If the user lacks the permission
        if not has_permission:
            raise exceptions.AjaxPermissionDeny()

        return super(PermissionRequiredMixin, self).dispatch(
            request, *args, **kwargs)


class ModelAccessibilityMixin(object):
    def dispatch(self, request, *args, **kwargs):
        base_model = self.get_object()
        # do nothing for the new case which model is none
        if base_model is None:
            return super(ModelAccessibilityMixin, self).dispatch(request, *args, **kwargs)
        if base_model and request.user.has_perm_access(base_model):
            if request.method == "GET" and 'check_access' in request.GET:
                return HttpResponseJson(exceptions.build_success_response_result(), request)
        else:
            raise exceptions.AjaxPermissionDeny()
        return super(ModelAccessibilityMixin, self).dispatch(request, *args, **kwargs)


class RequestAwareMixin(object):
    """
    A mixin to make "request" object available to Form.
    """
    def get_initial(self):
        initial = super(RequestAwareMixin, self).get_initial()
        initial["request"] = self.request
        return initial


class AjaxListView(AjaxLoginRequiredMixin, ListView):

    http_method_names = ['get']
    template_name = 'common/admin/generic.list.inc.html'


class FormProcessMixin(object):

    def form_valid(self, form):
        self.object = form.save()
        if hasattr(form, 'save_m2m'):
            try:
                # FIXME: it raise exception if the form is associated many2many with intermediary model
                # ignore it due to caller has done m2m saving.
                form.save_m2m()
            except:
                pass
        response_data = exceptions.build_success_response_result()
        response_data["id"] = self.object.id
        self.post_process(True, response_data)
        return HttpResponseJson(response_data, self.request)

    def form_invalid(self, form):
        self.post_process(False, form.errors)
        raise exceptions.AjaxValidateFormFailed(errors=form.errors)

    def post_process(self, is_success, response_data):
        pass


class ModalShowMixin(object):
    def get_context_data(self, **kwargs):
        context = super(ModalShowMixin, self).get_context_data(**kwargs)
        if self.request.GET.get('modal'):
            context['modal_show'] = True
        return context


class AjaxCreateView(AjaxLoginRequiredMixin, ActionUrlBuilderMixin, ModalShowMixin, FormProcessMixin, CreateView):

    http_method_names = ['get', 'post']
    form_action_url_name = ""
    template_name = 'common/admin/generic.form.inc.html'

    def get(self, request, *args, **kwargs):
        url = self.form_action_url_name or self.get_action_url(self.model, 'create')
        form_action = reverse(url)
        self.object = None
        form = self.get_form(self.get_form_class())
        return self.render_to_response(self.get_context_data(form_action=form_action, form=form))


class AjaxUpdateView(AjaxLoginRequiredMixin, ActionUrlBuilderMixin, ModalShowMixin, FormProcessMixin, UpdateView):

    http_method_names = ['get', 'post']
    form_action_url_name = ""
    template_name = 'common/admin/generic.form.inc.html'

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        url = self.form_action_url_name or self.get_action_url(self.model, 'edit')
        form_action = reverse(url, kwargs={'pk': pk})
        self.object = self.get_object()
        form = self.get_form(self.get_form_class())
        return self.render_to_response(self.get_context_data(form_action=form_action, form=form))


class AjaxFormView(AjaxLoginRequiredMixin, ActionUrlBuilderMixin, ModalShowMixin, FormProcessMixin, UpdateView):

    http_method_names = ['get', 'post']
    form_action_url_name = ""
    template_name = 'common/admin/generic.form.inc.html'

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if int(pk) == 0:
            return None
        return super(AjaxFormView, self).get_object(queryset)

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        url = self.form_action_url_name or self.get_action_url(self.model, 'edit')
        form_action = reverse(url, kwargs={'pk': pk})
        self.object = self.get_object()
        form = self.get_form(self.get_form_class())
        return self.render_to_response(self.get_context_data(form_action=form_action, form=form))


class AjaxFormsetEditView(AjaxLoginRequiredMixin, RequestAwareMixin, View):
    form_class = None
    formset_class = None
    master_model = None
    model = None
    form_action_url_name = ""
    master_list_url_name = ""
    template_name = 'common/admin/widget-box.formset.inc.html'
    http_method_names = ['get', 'post']
    # must be divide by 12 like 2, 3, 4, 6, 12 for follow the bootstrap span 12
    form_column_count = 3
    nested_model_verbose_name = u''
    master_model_verbose_name = u''

    def get_formset_initial(self):
        return None

    def get_initial(self):
        return {"request": self.request}

    def get_object(self):
        pk = self.kwargs.get('pk', None)
        return get_object_or_404(self.master_model, id=pk)

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if pk and int(pk) != 0:
            master = self.get_object()
        else:
            master = self.master_model()
        form_action = reverse(self.form_action_url_name, kwargs={'pk': pk})

        if 12 % self.form_column_count != 0:
            raise BaseException('form_column_count must be divide by 12 like 2, 3, 4, 6, 12 for follow the bootstrap col-md- 12')
        context_data = {
            'form': self.form_class(initial=self.get_initial(), instance=master) if self.form_class else None,
            'formset': self.formset_class(instance=master, initial=self.get_formset_initial(), prefix=self.model._meta.object_name.lower()),
            'form_action': form_action,
            'list_url': reverse(self.master_list_url_name),
            'model_verbose_name': self.model._meta.verbose_name,
            'master_model_verbose_name': self.master_model_verbose_name,
            'nested_model_verbose_name': self.nested_model_verbose_name,
            'object': master,
            'column_count': self.form_column_count,
            'helper': self.get_form_helper(),
        }
        return render_to_response(self.template_name,
                                  context_data,
                                  context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if pk and int(pk) != 0:
            master = self.get_object()
        else:
            master = self.master_model()
        form = None
        if self.form_class:
            form = self.form_class(request.POST, request.FILES, initial=self.get_initial(), instance=master)
            if not form.is_valid():
                raise exceptions.AjaxValidateFormFailed(errors=form.errors)

        formset = self.formset_class(request.POST, request.FILES, instance=master, prefix=self.model._meta.object_name.lower())
        if formset.is_valid():
            # XXX: should do form save only if formset is valid.
            if form:
                form.save()
            for fm in formset:
                # XXX: django formset will cache the fk value during construct the forms. So it has no effect after
                # change the fk value. So workaround to make fm to refresh the cache master fk value
                setattr(fm.instance, formset.fk.get_attname(), master.id)
                fm.request = request
                fm.save()
            try:
                formset.save_m2m()
            except:
                pass
            result = exceptions.build_success_response_result()
        else:
            # wrap the formset errors to a dict which is understand by client.
            counter = 0
            errors = {}
            for section_errors in formset.errors:
                if section_errors:
                    for key, value in section_errors.items():
                        errors[u"%s-%d-%s" % (self.model._meta.object_name.lower(), counter, key)] = value
                counter += 1
            raise exceptions.AjaxValidateFormFailed(errors=errors)
        return HttpResponseJson(result, request)

    def get_form_helper(self):
        return None


class AjaxTableInlineFormsetEditView(AjaxFormsetEditView):
    template_name = 'common/admin/table-inline.formset.inc.html'

    class TableInlineFormSetHelper(FormHelper):
        form_tag = False
        template = 'common/admin/bootstrap3/table_inline_formset.html'

    def get_form_helper(self):
        return AjaxTableInlineFormsetEditView.TableInlineFormSetHelper()


class AjaxNestedFormsetEditView(AjaxTableInlineFormsetEditView):
    template_name = 'common/admin/nested.formset.inc.html'


class AjaxSimpleUpdateView(AjaxLoginRequiredMixin, UpdateView):

    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        message = self.update(obj)
        if message:
            raise exceptions.AjaxValidateFormFailed(errors=message)
        return HttpResponseJson(exceptions.build_success_response_result(), request)

    def update(self, obj):
        return ""

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class ModelAwareBaseMixin(object):
    def get_context_data(self, **kwargs):
        context = super(ModelAwareBaseMixin, self).get_context_data(**kwargs)
        model_name = self.get_model_name()
        context['model_name'] = model_name
        context['model_verbose_name'] = self.model._meta.verbose_name
        context['form_id'] = "id_%s_%s_form" % (model_name, int(time.time()))
        # keep the current page path. So browser can refresh the page corretly.
        context['page_path'] = self.request.path
        return context

    def get_model_name(self):
        model_name = getattr(self, 'model_name', None)
        if not model_name:
            model_name = self.model._meta.object_name.lower()
        return model_name


class ModelAwareMixin(ModelAwareBaseMixin):
    """
    A mixin to inject some model useful information to context
    So we can make some common template code.
    NOTE: It require below naming conversion
    1. all of url must define a name mixed with namespace
    2. all of model must define a verbose_name
    """
    def get_context_data(self, **kwargs):
        context = super(ModelAwareMixin, self).get_context_data(**kwargs)
        namespace = getattr(self, 'app_label', None)
        if not namespace:
            namespace = self.model._meta.app_label
        namespace = self.get_ns_prefix() + namespace
        model_name = self.get_model_name()

        list_url = self.get_list_url()
        context['list_url'] = context.get('list_url', list_url or reverse('%s:%s_list' % (namespace, model_name)))
        context['edit_url'] = context.get('edit_url', '%s:%s_edit' % (namespace, model_name))
        context['delete_url'] = context.get('delete_url', '%s:%s_delete' % (namespace, model_name))
        context['datatables_list_url'] = context.get('datatables_list_url', context['list_url']+'.json/')
        try:
            if context.get('create_url') is None:
                context['create_url'] = context.get('create_url', reverse('%s:%s_create' % (namespace, model_name)))
        except NoReverseMatch:
            context['create_url'] = context.get('create_url', '')
        return context

    def get_ns_prefix(self):
        return 'admin:'

    def get_list_url(self):
        return ''


class ModelDetailView(ActionUrlBuilderMixin, DetailView):

    http_method_names = ['get']
    template_name = 'common/admin/model.detail.inc.html'
    related_sources = []

    def get(self, request, *args, **kwargs):
        if hasattr(self, "model_detail_class"):
            model = None
            model_detail_class = self.model_detail_class
        else:
            # use default one if child class doesn't specify "model_detail_class"
            model = self.model
            model_detail_class = ModelDetail

        model_detail = model_detail_class(self.request.user, self.kwargs.get(self.pk_url_kwarg, None), model)
        self.object = model_detail.instance

        builders = []
        for source in self.get_related_sources(self.object):
            model_class = source['modal_class']
            create_url = source.get('create_url')
            if not create_url:
                create_url = reverse(self.get_action_url(model_class, 'create'))
            builders.append({'datatables_builder': source['builder_class'],
                             'datatables_list_url': reverse(source['datatable_list_name'], kwargs={'pk': self.object.id}),
                             'model_name': model_class._meta.object_name,
                             'model_verbose_name': source.get('model_verbose_name', model_class._meta.verbose_name),
                             'create_url': create_url,
                             'modal_show': source.get('modal_show', False)})
        return self.render_to_response(self.get_context_data(object=self.object,
                                                             model=model_detail,
                                                             builders=builders,
                                                             page_path=self.request.path))

    def get_related_sources(self, master_model):
        return self.related_sources


class AjaxDatatablesView(AjaxLoginRequiredMixin, ListView):
    """
    app search and feed the result to jquery.datatables.
    the search result must match the defintion of jquery.datatables.
    see http://www.datatables.net/release-datatables/examples/data_sources/server_side.html
    """

    http_method_names = ['get']
    datatables_builder_class = None
    default_sort_field = None
    template_name = 'common/admin/generic.list.inc.html'

    def get_queryset(self):
        if "json" not in self.kwargs:
            return self.model.objects.none()
        return super(AjaxDatatablesView, self).get_queryset()

    def get(self, request,  *args, **kwargs):
        if "json" not in self.kwargs:
            return super(AjaxDatatablesView, self).get(request, *args, **kwargs)
        # sorting
        sorting_field = self.default_sort_field
        has_sorting_cols = int(request.GET.get('iSortingCols'))
        sorting_field_index = int(request.GET.get('iSortCol_0'))
        if has_sorting_cols and request.GET.get('bSortable_' + str(sorting_field_index)) == "true":
            # 目前只支持单一排序
            sorting_field = request.GET['mDataProp_' + str(sorting_field_index)]
            sorting_direction = request.GET.get('sSortDir_0')
            if sorting_direction == 'desc':
                sorting_field = '-' + sorting_field

        # searching
        searching_dict = {}
        for index in range(int(request.GET.get('iColumns'))):
            search_text = request.GET.get('sSearch_' + str(index))
            is_searchable = request.GET.get('bSearchable_' + str(index))
            if is_searchable == 'true' and search_text and search_text != 'null':
                field_name = request.GET['mDataProp_' + str(index)]
                search_expr = self.datatables_builder_class.base_fields[field_name].search_expr
                if not search_expr:
                    # 如果search表达式为空，则用属性名
                    search_expr = field_name
                    if isinstance(self.datatables_builder_class.base_fields[field_name], CharField):
                        # 如果是CharField，则用模糊查询
                        search_expr += '__icontains'
                    elif isinstance(self.datatables_builder_class.base_fields[field_name], ChoiceField):
                        search_expr += '__in'
                        searching_dict[search_expr] = search_text.split(',')

                searching_dict[search_expr] = searching_dict.get(search_expr) or search_text

        # paging
        queryset = self.get_queryset()
        if sorting_field:
            queryset = queryset.order_by(sorting_field)
        if searching_dict:
            queryset = queryset.filter(**searching_dict)

        total = queryset.count()

        data = []
        start = int(request.GET['iDisplayStart'])
        if int(request.GET['iDisplayLength']) < 0:
            end = sys.maxint
        else:
            end = start + int(request.GET['iDisplayLength'])
        for model_instance in queryset[start:end]:
             data.append(self.get_json_data(model_instance))
        res = {"sEcho": int(request.GET['sEcho']), "iTotalRecords": total, "iTotalDisplayRecords": total, "aaData": data}
        return HttpResponseJson(res, request)

    def get_json_data(self, model_instance):
        data = SortedDict()
        for name, builder_field in self.datatables_builder_class.base_fields.items():
            render = getattr(builder_field, 'render')
            if type(render) is FunctionType:
                val = render(self.request, model_instance, name)
            else:
                val = render.render(self.request, model_instance, name)
            if type(val) is StringType:
                val = SafeString(val).encode('utf-8')
            data[name] = val
        return data


class DatatablesBuilderMixin(object):

    def get_context_data(self, **kwargs):
            data = super(DatatablesBuilderMixin, self).get_context_data(**kwargs)
            data['datatables_builder'] = self.datatables_builder_class()
            datatables_list_url = self.get_datatables_list_url()
            if datatables_list_url:
                data['datatables_list_url'] = datatables_list_url
            return data

    def get_datatables_list_url(self):
        return ''


class ExcelExportView(ListView):

    http_method_names = ['get']
    excel_file_name = u'数据.xls'
    model_form_class = None
    col_width = {}

    def get(self, request, *args, **kwargs):
        excel_file_name = self.get_excel_file_name()
        queryset = self.get_queryset()
        form = self.model_form_class()
        book = Workbook(encoding='utf-8')
        sheet = book.add_sheet(excel_file_name)
        # write header
        header = ["ID"]
        header.extend(["%s" % field.label.encode('utf-8') for field in form])
        style = easyxf('alignment: wrap True')
        self.write_row_data(sheet.row(0), header, style)
        for i, field in enumerate(form):
            if field.name in self.col_width:
                sheet.col(i + 1).width = self.col_width[field.name]
        row_index = 1
        # write content
        for model in queryset:
            self.write_row_data(sheet.row(row_index), self.get_row_data(model, form), style)
            row_index += 1
        response = HttpResponse(content_type='application/ms-excel')
        book.save(response)
        response['Content-Disposition'] = 'attachment; filename="%s"' % excel_file_name.encode("utf-8")
        response['Cache-Control'] = 'no-cache'
        return response

    def write_row_data(self, row, data, style):
        index = 0
        for item in data:
            if isinstance(item, types.IntType):
                row.set_cell_number(index, item)
            else:
                row.write(index, item, style)
            index += 1

    def get_row_data(self, model, form):
        ret = [model.id]
        for form_field in form:
            try:
                model_field = self.model_form_class._meta.model._meta.get_field_by_name(form_field.name)[0]
            except FieldDoesNotExist as e:
                # raise the field not defined in form to subclass
                val = self.handle_unknown_field(model, form_field.name)
            else:
                #print model_field.attname, model_field.get_attname(), '=', getattr(obj, model_field.attname)
                val = model_field.value_to_string(model)
                if isinstance(model_field, django.db.models.fields.related.RelatedField):
                    if form_field.name == 'owner':
                        val = model.owner.get_full_name()
                    elif form_field.name == 'creator':
                        val = model.creator.get_full_name()
                    else:
                        val = self.handle_related_field(model, val, form_field.name, model_field)
                elif isinstance(model_field, django.db.models.fields.DateField) or \
                        isinstance(model_field, django.db.models.fields.DateTimeField):
                    date = getattr(model, model_field.attname, None)
                    if date:
                        val = utils.local_time_to_text(date)
                elif isinstance(model_field, django.db.models.fields.IntegerField):
                    val = int(val)
                    if model_field.choices:
                        display_method = getattr(model, 'get_%s_display' % model_field.attname, None)
                        if display_method:
                            display = display_method()
                            if display:
                                val = display
            if isinstance(val, types.StringType):
                ret.append(val.encode("utf-8"))
            else:
                ret.append(val)
        return ret

    def handle_unknown_field(self, model, field_name):
        logger.debug("handle_unknown_field %s:%s" % (model, field_name))
        return ""

    def handle_related_field(self, model, field_value, field_name, field):
        logger.debug("handle_related_field " + field_name + "  " + field_value)
        return field_value

    def get_excel_file_name(self):
        file_name = os.path.splitext(self.excel_file_name)[0]
        return "%s-%s.xls" % (file_name, datetime.datetime.now().strftime("%Y%m%d%H%M"))


class NavigationHomeMixin(object):
    def get_context_data(self, **kwargs):
        context = super(NavigationHomeMixin, self).get_context_data(**kwargs)
        context['hide_back_btn'] = True
        return context


class ModelActiveView(AjaxSimpleUpdateView):
    """
    Only work for one string field.
    Use 'unique_field_on_inactive' to defined field name if it's not the 'name'.
    """
    unique_field_on_inactive = 'name'

    def update(self, obj):
        obj.is_active = not obj.is_active
        if not obj.is_active:
            field_def = obj.__class__._meta.get_field_by_name(self.unique_field_on_inactive)
            if field_def:
                field = field_def[0]
                field_attr = getattr(obj, self.unique_field_on_inactive)
                id_attr = str(getattr(obj, 'id'))
                if field_attr and field and field.unique:
                    new_val = ('%s-%s' % (id_attr, field_attr))[0:field.max_length]
                    setattr(obj, self.unique_field_on_inactive, new_val)
        obj.save()


class AjaxDetailView(AjaxLoginRequiredMixin, DetailView):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data(object=self.object))


class HttpResponseJson(HttpResponse):
    def __init__(self, result, request=None, **extra):
        content_type = 'application/json; charset=utf-8'
        if request:
            # e.g.
            # Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)
            ua = request.META['HTTP_USER_AGENT']
            if ua and (ua.find('MSIE 8') != -1 or ua.find('MSIE 9') != -1):
                content_type = 'text/plain; charset=utf-8'

        super(HttpResponseJson, self).__init__(
            content=json.dumps(result, ensure_ascii=False),
            content_type=content_type, **extra)
