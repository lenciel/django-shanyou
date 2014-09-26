#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
from apps.common.admin.views import AjaxSimpleUpdateView, ModelAwareMixin, RequestAwareMixin, \
    NavigationHomeMixin, DatatablesBuilderMixin, AjaxDatatablesView, AjaxFormView
from apps.catalog.models import ProductCategory, Brand
from apps.catalog.forms import ProductCategoryDatatablesBuilder, ProductCategoryForm, \
    BrandDatatablesBuilder, BrandForm

HERE = os.path.dirname(__file__)
logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(HERE)) + '.' + os.path.basename(HERE))


def get_field_max_length(obj, name):
    return obj.__class__._meta.get_field_by_name(name)[0].max_length


class ProductCategoryListDatatablesView(NavigationHomeMixin, ModelAwareMixin, DatatablesBuilderMixin, AjaxDatatablesView):
    model = ProductCategory
    datatables_builder_class = ProductCategoryDatatablesBuilder
    queryset = ProductCategory.active_objects.all()


class ProductFormView(RequestAwareMixin, ModelAwareMixin, AjaxFormView):
    model = ProductCategory
    form_class = ProductCategoryForm


class ProductCategoryUpdateView(AjaxSimpleUpdateView):
    model = ProductCategory

    def update(self, obj):
        action_method = self.kwargs['action_method']
        msg = getattr(self, action_method)(obj)
        if msg:
            return msg
        if obj.id:
            obj.save()

    def delete(self, category):
        category.delete()
        #if category.has_children() or \
        #        Product.active_objects.filter(Q(category_level1=category) | Q(category_level2=category)):
        #    return u'该分类有未删除的子分类存在, 或者有关联的产品'
        #else:
        #    category.is_active = False
        #    category.name = ('%s-%s' % (category.id, category.name))[0:get_field_max_length(category, 'name')]
        #    category.save()


############### Brand #################

class BrandListDatatablesView(NavigationHomeMixin, ModelAwareMixin, DatatablesBuilderMixin, AjaxDatatablesView):
    model = Brand
    datatables_builder_class = BrandDatatablesBuilder
    queryset = Brand.objects.all()


class BrandFormView(RequestAwareMixin, ModelAwareMixin, AjaxFormView):
    model = Brand
    form_class = BrandForm


class BrandUpdateView(AjaxSimpleUpdateView):
    model = Brand

    def update(self, obj):
        action_method = self.kwargs['action_method']
        msg = getattr(self, action_method)(obj)
        if msg:
            return msg
        if obj.id:
            obj.save()

    def delete(self, brand):
        brand.delete()
