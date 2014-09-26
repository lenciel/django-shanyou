#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import OrderedDict
import logging
import os
from apps.common.models import BaseModel
from django.db import models
HERE = os.path.dirname(__file__)
logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(HERE)) + '.' + os.path.basename(HERE))


class ProductCategoryManager(models.Manager):
    def subcategories(self):
        """
        返回2级类别
        """
        return self.get_query_set().filter(parent__isnull=False).order_by('parent')

    def topcategories(self):
        """
        返回级类别
        """
        return self.get_query_set().filter(parent__isnull=True).order_by('parent')


class ProductCategory(BaseModel):
    _full_name_separator = ' > '

    name = models.CharField(max_length=64,
                            unique=True,
                            verbose_name=u'名称')

    code = models.CharField(max_length=32,
                            verbose_name=u'编号',
                            blank=True,
                            default="")

    full_name = models.CharField(max_length=128,
                                 verbose_name=u'全称',
                                 editable=False,)

    description = models.TextField(max_length=64,
                                   default='',
                                   blank=True,
                                   verbose_name=u'描述信息')

    # 第一级的上级分类为null
    parent = models.ForeignKey('self',
                               null=True,
                               blank=True,
                               verbose_name=u'上级分类')

    brands = models.ManyToManyField('Brand',
                                    verbose_name=u'关联品牌',
                                    through='BrandToProductCategory',
                                    related_name='categories')

    display_order = models.IntegerField(verbose_name=u'显示顺序',
                                        default=0,
                                        blank=True)

    objects = ProductCategoryManager()

    def update_fullname(self):
        """
        Updates the instance's full_name. Use update_children_full_names for updating
        the rest of the tree.
        """
        # If category has a parent, includes the parents slug in this one
        if self.is_top_category():
            self.full_name = self.name
        else:
            self.full_name = u'%s%s%s' % (
                self.parent.full_name, self._full_name_separator, self.name)

    def update_children_fullname(self):
        for category in ProductCategory.objects.filter(parent=self):
            category.update_fullname()
            category.save()

    def has_children(self):
        return ProductCategory.active_objects.filter(parent=self).count()

    def is_top_category(self):
        return self.parent is None

    def save(self, *args, **kwargs):
        self.update_fullname()
        super(ProductCategory, self).save(*args, **kwargs)
        if self.is_top_category():
            self.update_children_fullname()

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'产品分类'
        get_latest_by = ('updated',)
        ordering = ('display_order', 'name',)


class Brand(BaseModel):

    name = models.CharField(max_length=64,
                            unique=True,
                            verbose_name=u'名称')

    country = models.CharField(verbose_name=u'国家',
                               max_length=16,
                               blank=True,
                               default='')

    description = models.TextField(max_length=64,
                                   default='',
                                   blank=True,
                                   verbose_name=u'描述信息')

    display_order = models.IntegerField(verbose_name=u'显示顺序',
                                        default=0,
                                        blank=True)
    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'品牌'
        ordering = ('display_order', 'name',)
        get_latest_by = ('-updated',)


class BrandToProductCategoryManager(models.Manager):
    def group_by_category(self):
        categories = OrderedDict()
        for item in self.get_query_set().prefetch_related("brand", "product_category").order_by('product_category__display_order', "product_category__name"):
            if item.product_category.id not in categories:
                categories[item.product_category.id] = {"id": item.product_category.id, "name": item.product_category.name, "data": []}
            categories[item.product_category.id]["data"].append({"id": item.id})
        return categories


class BrandToProductCategory(models.Model):
    brand = models.ForeignKey('Brand',
                              verbose_name=u'品牌')

    product_category = models.ForeignKey('ProductCategory',
                                         verbose_name=u'类别')

    full_name = models.CharField(max_length=64,
                                 editable=False,
                                 verbose_name=u'名称')

    objects = BrandToProductCategoryManager()

    def __unicode__(self):
        return self.full_name

    def save(self, **kwargs):
        self.full_name = "%s%s" % (unicode(self.brand), unicode(self.product_category))
        super(BrandToProductCategory, self).save(**kwargs)

    class Meta:
        verbose_name = u'品牌类型'
        ordering = ('full_name',)
