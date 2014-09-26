#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from django.conf import settings
from django.db.models import signals, Max
from django.dispatch import receiver
import os
from django.db import models
from apps.common.models import BaseModel, TimeBaseModel

logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(__file__)))

CONTACT_METHOD_PHONE = 0
CONTACT_METHOD_EMAIL = 1
CONTACT_METHOD_SMS = 2
CONTACT_METHOD_QQ = 3
CONTACT_METHOD_FACE2FACE = 4
CONTACT_METHOD_OTHER = 5
CONTACT_METHOD_CHOICES = (
    (CONTACT_METHOD_PHONE, u'电话'),
    (CONTACT_METHOD_EMAIL, u'邮件'),
    (CONTACT_METHOD_SMS, u'短信'),
    (CONTACT_METHOD_QQ, u'QQ'),
    (CONTACT_METHOD_FACE2FACE, u'面谈'),
    (CONTACT_METHOD_OTHER, u'其他'),
)


class AbstractCustomer(BaseModel):
    phone = models.CharField(max_length=32,
                             unique=True,
                             verbose_name=u'电话')

    address = models.CharField(max_length=128,
                               blank=True,
                               default='',
                               verbose_name=u'地址')

    qq = models.CharField(max_length=16,
                          blank=True,
                          default='',
                          verbose_name='QQ')

    #wechat在不为空情况下必须唯一, 需要通过代码来检查唯一性
    wechat = models.CharField(max_length=32,
                              verbose_name=u'微信号',
                              blank=True,
                              default='')

    email = models.EmailField(max_length=64,
                              blank=True,
                              default="")

    description = models.TextField(max_length=1024,
                                   blank=True,
                                   default='',
                                   verbose_name=u'备注')

    key_days = models.TextField(blank=True,
                                default='',
                                help_text=u'以json格式存放. {"name":"xxx", "key_day": "2011-01-01", "description": "xxxx"}',
                                verbose_name=u'个人重要日期')

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name


class Customer(AbstractCustomer):
    name = models.CharField(verbose_name='名称',
                            max_length=30)

    partner = models.ForeignKey("Partner",
                                verbose_name=u'合作伙伴',
                                related_name='customers',
                                blank=True,
                                null=True)

    CHANNEL_TYPE_PARTNER = 0
    CHANNEL_TYPE_OWN = 1
    CHANNEL_TYPE_ESTATE = 2
    CHANNEL_TYPE_DECORATOR = 3
    CHANNEL_TYPE_OTHER = 4
    CHANNEL_TYPE_CHOICES = (
        (CHANNEL_TYPE_PARTNER, u'合作伙伴'),
        (CHANNEL_TYPE_OWN, u'自有开发'),
        (CHANNEL_TYPE_ESTATE, u'物业公司'),
        (CHANNEL_TYPE_DECORATOR, u'装饰公司'),
        (CHANNEL_TYPE_OTHER, u'其他'),
    )
    channel_type = models.IntegerField(choices=CHANNEL_TYPE_CHOICES,
                                       verbose_name=u'渠道类型',
                                       default=CHANNEL_TYPE_PARTNER)

    class Meta:
        verbose_name = u'客户'
        ordering = ('-updated',)


class Partner(AbstractCustomer):
    name = models.CharField(verbose_name=u'公司名称',
                            max_length=30)

    mobile = models.CharField(max_length=32,
                                  verbose_name=u'手机号码',
                                  blank=True,
                                  default='')

    contacts = models.CharField(verbose_name='联系人',
                                blank=False,
                                null=True,
                                max_length=64)

    last_contact_date = models.DateTimeField(verbose_name=u'最近联系日期',
                                             help_text=u'伙伴跟踪记录的最大日期',
                                             null=True,
                                             editable=False)

    #战略伙伴、网络资源、广告回访、朋友介绍、物业管理、公司资源、设计师
    PARTNER_TYPE_STRATEGY = 0
    PARTNER_TYPE_NETWORK = 1
    PARTNER_TYPE_AD = 2
    PARTNER_TYPE_INTRODUCTION = 3
    PARTNER_TYPE_PROPERTY = 4
    PARTNER_TYPE_COMPANY = 5
    PARTNER_TYPE_DESIGNER = 6
    PARTNER_TYPE_CHOICES = (
        (PARTNER_TYPE_STRATEGY, u'战略伙伴'),
        (PARTNER_TYPE_NETWORK, u'网络资源'),
        (PARTNER_TYPE_AD, u'广告回访'),
        (PARTNER_TYPE_INTRODUCTION, u'朋友介绍'),
        (PARTNER_TYPE_PROPERTY, u'物业管理'),
        (PARTNER_TYPE_COMPANY, u'公司资源'),
        (PARTNER_TYPE_DESIGNER, u'设计师'),
    )
    type = models.IntegerField(verbose_name=u'类型',
                               choices=PARTNER_TYPE_CHOICES,
                               default=PARTNER_TYPE_STRATEGY)

    class Meta:
        verbose_name = u'合作伙伴'
        ordering = ('-updated',)

    def __unicode__(self):
        return self.contacts or u''

class TrackingBaseModel(TimeBaseModel):
    contact_method = models.IntegerField(choices=CONTACT_METHOD_CHOICES,
                                         default=CONTACT_METHOD_PHONE,
                                         verbose_name=u'接触方式')

    contact_date = models.DateTimeField(verbose_name=u'联系时间')

    description = models.TextField(blank=True,
                                   default='',
                                   verbose_name=u'描述')

    question = models.TextField(blank=True,
                                default='',
                                verbose_name=u'客户问题')

    solution = models.TextField(blank=True,
                                default='',
                                verbose_name=u'解决方案')

    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                verbose_name=u'创建人',
                                related_name='+')

    class Meta:
        abstract = True


class PartnerTracking(TrackingBaseModel):

    partner = models.ForeignKey(Partner,
                                verbose_name=u'合作伙伴',
                                related_name='trackings')

    def __unicode__(self):
        return "%s-%s" % (unicode(self.partner), self.get_contact_method_display())

    class Meta:
        verbose_name = u'沟通记录'
        ordering = ('-updated',)


@receiver(signals.post_save, sender=PartnerTracking)
def handle_partnertracking_changed(sender, **kwargs):
    tracking = kwargs['instance']
    q = PartnerTracking.objects.filter(partner=tracking.partner).annotate(max_contact_date=Max('contact_date'))
    Partner.objects.filter(id=tracking.partner.id).update(last_contact_date=q[0].max_contact_date)
