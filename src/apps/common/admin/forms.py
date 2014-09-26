#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from crispy_forms.helper import FormHelper
import os
from django import forms
import django
from django.contrib.auth import get_user_model
from django.db.models import FieldDoesNotExist
import utils


HERE = os.path.dirname(__file__)
logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(HERE)) + '.' + os.path.basename(HERE))


class UserModelChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        if not kwargs.get('queryset'):
            kwargs['queryset'] = get_user_model().staffs.active_objects().only("real_name").order_by('real_name')
        super(UserModelChoiceField, self).__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        return obj.get_full_name()


class UserMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name()


class DisplayCreatorOwnerMixin(object):
    def get_owner_display(self, model):
        return model.owner.get_full_name()

    def get_creator_display(self, model):
        return model.creator.get_full_name()


class ModelDetail(DisplayCreatorOwnerMixin, object):
    """
    For related fields, __unicode__ method would be the default choice to display in django templates. If a sub-class
    has special display logic, it could implement a static method(@staticmethod) named "get_{field name}_display" to
    customize the output.
    """

    def __init__(self, user, pk=None, model=None, instance=None):
        if not model:
            opts = self.Meta
            if opts.model is None:
                raise ValueError('ModelDetail has no model class specified.')
            model = opts.model
        self._meta = {'model': model}
        self._initial_meta()
        self.pk = pk
        self.instance = instance or self._fetch_model()
        self.user = user
        self.expanded = False

    def _initial_meta(self):
        for attr in ['includes', 'excludes', 'related_fields', 'prefetch_fields', 'fields_order']:
            self._meta[attr] = getattr(self.Meta, attr, None)

    def detail(self):
        ret = []
        if not self.instance:
            return ret
        for f in self._fields_for_model():
            val = self._detail_field(f)
            if val:
                ret.append(val)
        return sorted(ret, key=lambda r: self._display_index(r['name'], len(ret)))

    def __unicode__(self):
        return unicode(self.instance)

    def related_fields(self):
        ret = {}
        if not self._meta['prefetch_fields']:
            return ret

        self.expanded = True

        for p in self._meta['prefetch_fields']:
            rs = getattr(self.instance, p).all()
            if not rs:
                continue
            mid = []
            for r in rs:
                m = ModelDetail(self.user, pk=r.id, instance=r, model=r.__class__)
                mid.append(m)
            ret[r._meta.verbose_name] = mid
        return ret

    def _display_index(self, field_name, default_index):
        f_order = self._meta.get('fields_order', None)
        return f_order.index(field_name) if f_order and field_name in f_order else default_index

    def _fetch_model(self):
        objects_manager = self._meta['model'].objects
        if self._meta['related_fields']:
            queryset = objects_manager.select_related(*self._meta['related_fields'])
        else:
            queryset = objects_manager.select_related()
        if self._meta['prefetch_fields']:
            queryset = queryset.prefetch_related(*self._meta['prefetch_fields'])
        return queryset.get(pk=self.pk)

    def _detail_field(self, field):
        fname = field.name
        val = getattr(self.instance, fname)
        func_name = 'get_%s_display' % fname
        func = getattr(self, func_name) if hasattr(self, func_name) else None
        if func:
            val = func(self.instance)
        elif isinstance(field, django.db.models.fields.IntegerField):
            if field.choices:
                display_method = getattr(self.instance, 'get_%s_display' % fname, None)
                display_val = display_method() if display_method else None
                val = display_val or val
        elif isinstance(field, django.db.models.fields.DateField):
            val = utils.local_time_to_text(val) if val else None
        elif isinstance(field, django.db.models.fields.related.ManyToManyField):
            return None

        return {'label': field.verbose_name or fname,
                'name': fname,
                'value': val or ''}

    def _fields_for_model(self):
        meta_fields = self._meta['model']._meta._name_map
        if self._meta['excludes']:
            return (v[0] for k, v in meta_fields.items() if v[2] and k not in self._meta['excludes'])
        elif self._meta['includes']:
            return (v[0] for k, v in meta_fields.items() if v[2] and k in self._meta['includes'])
        else:
            return (v[0] for k, v in meta_fields.items() if v[2])

    class Meta:
        excludes = ('is_active', 'id', )


class BootstrapFormHelper(FormHelper):
    form_class = 'form-horizontal'
    label_class = 'col-lg-2'
    field_class = 'col-lg-8'
    form_tag = False


class CrispyModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(CrispyModelForm, self).__init__(*args, **kwargs)
        should_focus = True
        for field in self.fields.values():
            css_class = ""
            if field.required:
                css_class = "required"
            if isinstance(field, forms.IntegerField):
                css_class += " number"
            if isinstance(field, forms.DateField):
                css_class += " date"
            if css_class:
                field.widget.attrs['class'] = css_class
            if should_focus:
                field.widget.attrs["autofocus"] = "autofocus"
                should_focus = False
        self.helper = BootstrapFormHelper(self)

