#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models


class ActiveDataManager(models.Manager):
    def get_query_set(self):
        return super(ActiveDataManager, self).get_query_set().filter(is_active=True)


class TimeBaseModel(models.Model):
    created = models.DateTimeField(verbose_name=u'创建时间',
                                   auto_now_add=True)

    updated = models.DateTimeField(verbose_name=u'更新时间',
                                   auto_now=True,
                                   db_index=True)

    def updated_timestamp(self):
        return int(self.updated.strftime("%s")) if self.updated else 0

    def created_timestamp(self):
        return int(self.created.strftime("%s")) if self.created else 0

    class Meta:
        abstract = True



class BaseModel(TimeBaseModel):

    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              verbose_name=u'跟进人',
                              related_name='+',
                              null=True)

    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                verbose_name=u'创建人',
                                related_name='+')

    is_active = models.BooleanField(default=True,
                                    verbose_name=u'激活状态')

    objects = models.Manager()

    active_objects = ActiveDataManager()

    def get_owner(self):
        return self.owner

    class Meta:
        abstract = True
