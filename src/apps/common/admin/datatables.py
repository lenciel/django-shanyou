#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import os
from types import FunctionType, MethodType

from django import forms
import django
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db.models import FieldDoesNotExist
from django.utils.safestring import SafeString
import utils

HERE = os.path.dirname(__file__)
logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(HERE)) + '.' + os.path.basename(HERE))


class DatatablesColumnSimpleRender(object):
    def render(self, request, model, field_name):
        try:
            model_field = model._meta.get_field_by_name(field_name)[0]
        except FieldDoesNotExist as e:
            if hasattr(model, field_name):
                return getattr(model, field_name)()
            else:
                raise e
        #print model_field.attname, model_field.get_attname(), '=', getattr(obj, model_field.attname)
        val = model_field.value_to_string(model)
        if isinstance(model_field, django.db.models.fields.related.RelatedField):
            if field_name == 'owner':
                val = model.owner.get_full_name()
            elif field_name == 'creator':
                val = model.creator.get_full_name()
            else:
                val = unicode(getattr(model, field_name))
        elif isinstance(model_field, django.db.models.fields.DateTimeField):
            date = getattr(model, model_field.attname, None)
            val = utils.local_time_to_text(date)
        elif isinstance(model_field, django.db.models.fields.DateField):
            date = getattr(model, model_field.attname, None)
            val = utils.local_date_to_text(date)
        elif isinstance(model_field, django.db.models.fields.BooleanField):
            val = u'是' if val == 'True' else u'否'
        elif isinstance(model_field, django.db.models.fields.IntegerField) or \
             isinstance(model_field, django.db.models.fields.CharField):

            if model_field.choices:
                display_method = getattr(model, 'get_%s_display' % model_field.attname, None)
                if display_method:
                    display = display_method()
                    if display:
                        val = display

        return val if val != "None" else ""


class DatatablesColumnActionsRender(object):
    DEFAULT_EXPAND_THRESHOLD = 2
    expand_threshold = DEFAULT_EXPAND_THRESHOLD

    def __init__(self, actions=None, action_permission=None):
        self.action_permission = action_permission
        if actions is None:
            self.actions = \
                [{'is_link': True,  'name': 'edit', 'text': u'编辑', 'icon': 'icon-edit'},
                 {'is_link': False, 'name': 'delete', 'text': u'删除', 'icon': 'icon-remove'},]
        else:
            self.actions = actions

    def render(self, request, model, field_name):
        if not self.actions:
            return ""

        if self.action_permission:
            has_permission = request.user.is_superuser or request.user.has_perm(self.action_permission)
            # If the user lacks the permission
            if not has_permission:
                return ""

        namespace = "admin:" + model._meta.app_label
        model_name = model._meta.object_name.lower()
        action_items = []
        for action in self.actions:
            is_link = action['is_link']
            name = action['name']
            url = action.get('url')
            if not url:
                url_name = action.get('url_name', '%s:%s_%s' % (namespace, model_name, name))
                url = reverse(url_name, kwargs={'pk': model.id})
            icon = action['icon']
            text = action['text']
            extra = action.get('extra') or {}
            extra_json = SafeString(json.dumps(extra))
            action_type = action.get('action_type') or 'GET'
            handler_type = action.get('handler_type') or 'system'
            modal_tag = "modal" if action.get('modal_show', False) else ""
            check_access = "data-check_access='true'" if action.get('check_access') else ""
            if is_link:
                template = u'''
<a href='#' data-action='%(name)s' data-extra='%(extra_json)s' data-text='%(text)s' data-%(modal_tag)surl='%(url)s' \
data-handlertype='%(handler_type)s' %(check_access)s> <i class='%(icon)s'></i> %(text)s</a>'''
            else:
                template = u'''
<a href='#action' data-action='%(name)s' data-extra='%(extra_json)s' data-text='%(text)s' \
data-actiontype='%(action_type)s' data-%(modal_tag)surl='%(url)s' data-handlertype='%(handler_type)s' %(check_access)s> \
<i class='%(icon)s'></i> %(text)s</a>'''
            action_items.append(template % locals())

        actions_str = ""

        if self.expand_threshold < len(self.actions):
            for item in action_items:
                actions_str += "<li>" + item + "</li>"
            html = u'''
<div class="btn-group">
  <button data-toggle="dropdown" class="btn btn-primary dropdown-toggle btn-sm">操作<span class="caret"></span></button>
  <ul class="pull-right dropdown-menu action-button">%s</ul>
</div>'''
        else:
            actions_str = "<br/>".join(action_items)
            html = u'<div class="btn-group">%s</div>'

        return html % actions_str


class DatatablesColumnImageRender(object):

    def render(self, request, model, field_name):
        if hasattr(model, field_name):
            attr = getattr(model, field_name)
            if type(attr) is FunctionType or type(attr) is MethodType:
                url = attr()
            else:
                url = attr.url if attr else ""
        else:
            raise NotImplemented("Invalid field name for image ")
        return '<img class="small-icon" src="%s">' % url if url else ""


class DatatablesColumnDateRender(object):

    def render(self, request, model, field_name):
        if hasattr(model, field_name):
            attr = getattr(model, field_name)
            if type(attr) is FunctionType or type(attr) is MethodType:
                date = attr()
            else:
                date = attr
        else:
            raise NotImplemented("Invalid field for date ")
        return utils.local_date_to_text(date)


class DatatablesColumnMixin(object):
    def __init__(self, *args, **kwargs):
        self.is_sortable = kwargs.pop('is_sortable', False)
        self.is_visible = kwargs.pop('is_visible', True)
        self.is_searchable = kwargs.pop('is_searchable', False)
        self.col_width = kwargs.pop('col_width', '')
        self.search_expr = kwargs.pop('search_expr', '')
        self.css_class = kwargs.pop('css_class', '')
        self.render = kwargs.pop('render', DatatablesColumnSimpleRender())
        self.is_checkbox = kwargs.pop('is_checkbox', False)
        super(DatatablesColumnMixin, self).__init__(*args, **kwargs)


class DatatablesTextColumn(DatatablesColumnMixin, forms.CharField):
    def __init__(self, *args, **kwargs):
        link_resolve = kwargs.pop('link_resolve', None)
        if link_resolve:
            if kwargs.pop('access_check', None):
                url_tag = '<a href="#" data-check_access="true" data-url="%s">%s</a>'
            else:
                url_tag = '<a href="#" data-url="%s">%s</a>'
            kwargs['render'] = kwargs.get('render', (lambda request, model, field_name: url_tag % link_resolve(request, model, field_name)))

        super(DatatablesTextColumn, self).__init__(*args, **kwargs)
        self.widget.attrs['class'] = self.css_class or 'input-small'


class DatatablesModelChoiceColumn(DatatablesColumnMixin, forms.ModelMultipleChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs['is_sortable'] = kwargs.get('is_sortable', True)
        super(DatatablesModelChoiceColumn, self).__init__(*args, **kwargs)


class DatatablesUserChoiceColumn(DatatablesModelChoiceColumn):
    def __init__(self, *args, **kwargs):
       super(DatatablesUserChoiceColumn, self).__init__(is_searchable=True,
                                                        queryset=get_user_model().staffs.active_objects().only('real_name'),
                                                        col_width="6%",
                                                        *args, **kwargs)

    def label_from_instance(self, obj):
        return obj.get_full_name()


class DatatablesChoiceColumn(DatatablesColumnMixin, forms.MultipleChoiceField):

    def __init__(self, choices, *args, **kwargs):
        kwargs['choices'] = choices
        super(DatatablesChoiceColumn, self).__init__(*args, **kwargs)


class DatatablesBooleanColumn(DatatablesColumnMixin, forms.ChoiceField):

    def __init__(self, choices=None, *args, **kwargs):
        kwargs['choices'] = choices or (('', u'全部'), (1, u'是'), (0, '否'))
        kwargs['is_sortable'] = kwargs.get('is_sortable', True)
        super(DatatablesBooleanColumn, self).__init__(*args, **kwargs)


class DatatablesDateTimeColumn(DatatablesColumnMixin, forms.DateTimeField):

    def __init__(self, *args, **kwargs):
        kwargs['col_width'] = kwargs.get('col_width', "8%")
        kwargs['is_sortable'] = kwargs.get('is_sortable', True)
        super(DatatablesDateTimeColumn, self).__init__(*args, **kwargs)


class DatatablesDateColumn(DatatablesColumnMixin, forms.DateField):

    def __init__(self, *args, **kwargs):
        kwargs['col_width'] = kwargs.get('col_width', "8%")
        kwargs['is_sortable'] = kwargs.get('is_sortable', True)
        kwargs['render'] = kwargs.get('render') or DatatablesColumnDateRender()
        super(DatatablesDateColumn, self).__init__(*args, **kwargs)


class DatatablesImageColumn(DatatablesTextColumn):

    def __init__(self, *args, **kwargs):
        kwargs['col_width'] = kwargs.get('col_width', "5%")
        kwargs['render'] = kwargs.get('render') or DatatablesColumnImageRender()
        super(DatatablesImageColumn, self).__init__(*args, **kwargs)


class DatatablesIntegerColumn(DatatablesTextColumn):

    def __init__(self, *args, **kwargs):
        kwargs['col_width'] = kwargs.get('col_width', "5%")
        super(DatatablesIntegerColumn, self).__init__(*args, **kwargs)


class DatatablesIdColumn(DatatablesTextColumn):

    def __init__(self, *args, **kwargs):
        kwargs['col_width'] = kwargs.get('col_width', "3%")
        kwargs['is_visible'] = kwargs.get('is_visible', False)
        kwargs['is_searchable'] = kwargs.get('is_searchable', True)
        super(DatatablesIdColumn, self).__init__(*args, label='ID', **kwargs)


class DatatablesActionsColumn(DatatablesColumnMixin, forms.CharField):

    def __init__(self, *args, **kwargs):
        # set a default render
        kwargs['render'] = kwargs.get('render', DatatablesColumnActionsRender(actions=kwargs.pop("actions", None),
                                                                              action_permission=kwargs.pop("action_permission", None)),)
        kwargs['col_width'] = kwargs.get('col_width', "6%")
        super(DatatablesActionsColumn, self).__init__(*args, label='', **kwargs)


class DatatablesCheckboxColumn(DatatablesColumnMixin, forms.CharField):

    def __init__(self, *args, **kwargs):
        # set a default render
        kwargs['render'] = kwargs.get('render', (lambda request, model, field_name:
                                                 '<input type="checkbox" name="id-%s-%d"/><span class="lbl"></span>' % (field_name, model.id)))
        kwargs['col_width'] = kwargs.get('col_width', "2%")
        kwargs['is_checkbox'] = kwargs.get('is_checkbox', True)

        super(DatatablesCheckboxColumn, self).__init__(*args, label='', **kwargs)


class DatatablesBuilder(forms.Form):

    def build_aoColumnDefs(self):
        """
        see http://www.datatables.net/usage/columns
        """
        ret = []
        index = 0
        for name, field in self.fields.items():
            label = field.label
            is_sys_field = name.startswith("_")
            if not label and not is_sys_field:
                label = self.Meta.model._meta.get_field_by_name(name)[0].verbose_name
            entry = {'sName': name, 'sTitle': label, 'bSortable': field.is_sortable,
                     'bVisible': field.is_visible, 'aTargets': [index], 'mData': name,
                     'bSearchable': field.is_searchable, }
            if field.col_width:
                entry['sWidth'] = field.col_width
            ret.append(entry)
            index += 1
        return SafeString(json.dumps(ret))


class DatatablesItemsColumn(DatatablesColumnMixin, forms.CharField):

    def __init__(self, *args, **kwargs):
        # set a default render
        kwargs['render'] = kwargs.get('render', DatatablesColumnItemsRender(items=kwargs.pop("items", None)))
        kwargs['col_width'] = kwargs.get('col_width', "5%")
        super(DatatablesItemsColumn, self).__init__(*args, **kwargs)


class DatatablesColumnItemsRender(object):
    def __init__(self, items=None):
        self.items = items

    def render(self, request, model):
        if not self.items:
            return ""

        namespace = "admin:" + model._meta.app_label
        model_name = model._meta.object_name.lower()
        sum = "%s" % len(self.items)
        item_list = ""
        for item in self.items:
            name = item['name']
            url = item.get('url')
            if not url:
                url_name = item.get('url_name', '%s:%s_%s' % (namespace, model_name, name))
                url = reverse(url_name, kwargs={'pk': item['id']})
            text = item['text']
            check_access = "data-check_access='true'" if item.get('check_access') else ""

            template = u'''
<li><a href='#' data-action='%(name)s' data-text='%(text)s' data-url='%(url)s' %(check_access)s> %(text)s</a></li>'''
            item_list += template % locals()
        html = u'''
<div class="btn-group">
  <button data-toggle="dropdown" class="btn btn-yellow dropdown-toggle btn-sm">%s<span class="caret"></span></button>
  <ul class="pull-right dropdown-menu action-button">%s</ul>
</div>'''
        return html % (sum, item_list)
