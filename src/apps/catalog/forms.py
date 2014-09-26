#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from crispy_forms.bootstrap import InlineCheckboxes
import os
from django.core.urlresolvers import reverse
from apps.common.admin.datatables import DatatablesIdColumn, DatatablesBuilder, DatatablesTextColumn, \
    DatatablesColumnActionsRender, \
    DatatablesActionsColumn
from apps.catalog.models import ProductCategory, Brand, BrandToProductCategory
from apps.common.admin.forms import CrispyModelForm

logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(__file__)))


class ProductCategoryForm(CrispyModelForm):
    def __init__(self, *args, **kwargs):
        super(ProductCategoryForm, self).__init__(*args, **kwargs)

        self.fields['brands'].queryset = Brand.active_objects.only("name")
        # disable the no-sense help text
        self.fields['brands'].help_text = u''
        brands_index = self.helper['brands'].slice[0][0][0]
        self.helper[brands_index] = InlineCheckboxes('brands')
        #self.fields['parent'].queryset = ProductCategory.objects.topcategories().filter(is_active=True)
        #if kwargs['instance']:
        #    self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(pk=kwargs['instance'].pk)

    class Meta:
        model = ProductCategory
        fields = ('name', 'code', 'brands', 'display_order', 'description')

    def save(self, commit=False):
        category = super(ProductCategoryForm, self).save(commit)
        category.creator = self.initial['request'].user
        category.save()

        category.brands.clear()
        for brand in self.cleaned_data['brands']:
            BrandToProductCategory(product_category=category, brand=brand).save()
        return category


class ProductCategoryDatatablesBuilder(DatatablesBuilder):
    id = DatatablesIdColumn()

    code = DatatablesTextColumn(is_searchable=True,
                                col_width="10%")

    name = DatatablesTextColumn(is_searchable=True)

    #full_name = DatatablesTextColumn(label=u'全称', )

    description = DatatablesTextColumn()

    #parent = DatatablesModelChoiceColumn(label=u'上级分类',
    #                                     is_searchable=True,
    #                                     queryset=ProductCategory.active_objects.only('name').all())

    def actions_render(request, model, field_name):
        action_url_builder = lambda model, action: reverse('admin:catalog:productcategory_update',
                                                           kwargs={'pk': model.id, 'action_method': action})

        actions = [{'is_link': True, 'name': 'edit', 'text': u'编辑', 'icon': 'icon-edit', 'url_name': 'admin:catalog:productcategory_edit'},
                   {'is_link': False, 'name': 'lock', 'text': u'删除', 'icon': 'icon-remove', "url": action_url_builder(model, "delete")}]
        return DatatablesColumnActionsRender(actions).render(request, model, field_name)

    _actions = DatatablesActionsColumn(render=actions_render)

    class Meta:
        model = ProductCategory

class BrandForm(CrispyModelForm):

    class Meta:
        model = Brand
        fields = ('name', 'country', 'display_order', 'description')

    def save(self, commit=False):
        brand = super(BrandForm, self).save(commit)
        if not hasattr(brand, "creator"):
            brand.creator = self.initial['request'].user
        brand.save()
        return brand


class BrandDatatablesBuilder(DatatablesBuilder):
    id = DatatablesIdColumn()

    name = DatatablesTextColumn(is_searchable=True)

    country = DatatablesTextColumn(is_searchable=True)

    description = DatatablesTextColumn()

    def actions_render(request, model, field_name):
        action_url_builder = lambda model, action: reverse('admin:catalog:brand_update',
                                                           kwargs={'pk': model.id, 'action_method': action})
        actions = [{'is_link': True, 'name': 'edit', 'text': u'编辑', 'icon': 'icon-edit'},
                   {'is_link': False, 'name': 'lock', 'text': u'删除', 'icon': 'icon-remove',
                    "url": action_url_builder(model, "delete")}]
        return DatatablesColumnActionsRender(actions=actions).render(request, model, field_name)

    _actions = DatatablesActionsColumn(render=actions_render)

    class Meta:
        model = Brand
