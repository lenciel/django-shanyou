#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from django.conf import settings
from django.db.models import signals, Max
from django.dispatch import receiver
import os
from django.db import models
from apps.catalog.models import BrandToProductCategory
from apps.common.models import BaseModel, TimeBaseModel
from apps.customer.models import Customer, CONTACT_METHOD_CHOICES, CONTACT_METHOD_PHONE, TrackingBaseModel

logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(__file__)))


class Building(BaseModel):

    name = models.CharField(max_length=128,
                            verbose_name=u'名称')

    province = models.CharField(max_length=16,
                                verbose_name=u'省',
                                default=u'四川省')

    city = models.CharField(max_length=16,
                            verbose_name=u'城市',
                            default=u'成都市')

    district = models.CharField(max_length=32,
                                verbose_name=u'区',
                                default=u'武侯区')

    address = models.CharField(max_length=128,
                               verbose_name=u'楼盘地址',
                               blank=True,
                               default='')

    # Full name which represents the total identity information in the form of
    # 'name' + '(' + 'city' + ')'. For example: 保利星座（成都市）
    # See: save()
    full_name = models.TextField(max_length=512,
                                 verbose_name=u'详细地址',
                                 editable=False)

    developer = models.CharField(max_length=128,
                                 blank=True,
                                 default='',
                                 verbose_name=u'开发商')

    avg_price_min = models.PositiveIntegerField(verbose_name=u'最低单价(千元/平米)',
                                                blank=True,
                                                default=0)

    avg_price_max = models.PositiveIntegerField(verbose_name=u'最高单价(千元/平米)',
                                                blank=True,
                                                default=0)

    total_price_min = models.PositiveIntegerField(verbose_name=u'最低总价(万元)',
                                                  blank=True,
                                                  default=0)

    total_price_max = models.PositiveIntegerField(verbose_name=u'最高总价(万元)',
                                                  blank=True,
                                                  default=0)

    amount = models.PositiveIntegerField(verbose_name=u'户数',
                                         blank=True,
                                         default=0)

    description = models.TextField(max_length=512,
                                   blank=True,
                                   default='',
                                   verbose_name=u'描述')

    property_management = models.CharField(verbose_name=u'物管公司',
                                           max_length=128,
                                           blank=True,
                                           default='')

    def __unicode__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        self.full_name = "%s (%s)" % (self.name, self.city)
        super(Building, self).save(*args, **kwargs)

    class Meta:
        verbose_name = u'楼盘'
        unique_together = ('province', 'city', 'district', 'address', 'name')
        ordering = ('-updated',)


class Project(BaseModel):

    building = models.ForeignKey(Building,
                                 verbose_name=u'楼盘',
                                 related_name='projects')

    house_number = models.CharField(max_length=32,
                                    verbose_name=u'门牌号码')

    # customer 和 合作伙伴必须有一个
    customer = models.ForeignKey(Customer,
                                 verbose_name=u'关联客户',
                                 related_name='projects')

    # 联系人，不一定是客户本人
    contacts = models.CharField(max_length=32,
                                verbose_name=u'联系人',
                                blank=True,
                                default='')

    # 联系人电话，不作唯一判断
    phone = models.CharField(max_length=32,
                             verbose_name=u'联系电话',
                             blank=True,
                             default='')

    WILLING_A = 'a'
    WILLING_B = 'b'
    WILLING_C = 'c'
    WILLING_D = 'd'
    WILLING_S_SIGNED = 's'
    WILLING_R = 'r'
    WILLING_O = 'o'
    WILLING_CHOICES = (
        (WILLING_A, WILLING_A),
        (WILLING_B, WILLING_B),
        (WILLING_C, WILLING_C),
        (WILLING_D, WILLING_D),
        (WILLING_S_SIGNED, WILLING_S_SIGNED),
        (WILLING_R, WILLING_R),
        (WILLING_O, WILLING_O),
    )

    willing = models.CharField(choices=WILLING_CHOICES,
                               max_length=1,
                               default=WILLING_A,
                               verbose_name=u'销售状态',
                               help_text='''
<ul><li>a-非常意向签约的，销售机会是80%以上</li>
<li>b-深度面谈过，出了方案，比较有意向签约的客户，销售机会是60%以上</li>
<li>c-拿了图纸或者去过现场，电话简单沟通过，销售机会30%～50%</li>
<li>d-尚未深度沟通或者出方案，销售机会30%以下</li>
<li>s-签约客户</li>
<li>r-失败客户</li>
<li>o-质保期已过客户</li><ul>''')

    # 项目状态，是指 协调现场、设备订货、设备到货、隐蔽施工、隐蔽完成、室外安装、调试设备、客户验收、客户交付、质保中
    # 公司根据工程节点划分的状态，有点类似于京东的发货流程
    CONTRACT_STATUS_NONE = 0
    CONTRACT_STATUS_ONSITE = 1
    CONTRACT_STATUS_ORDER = 2
    CONTRACT_STATUS_RECEIVE = 3
    CONTRACT_STATUS_HIDE_OPERATION = 4
    CONTRACT_STATUS_HIDE_COMPLETE = 5
    CONTRACT_STATUS_HIDE_INSTALL = 6
    CONTRACT_STATUS_DEBUG = 7
    CONTRACT_STATUS_ACCEPT = 8
    CONTRACT_STATUS_DELIVER = 9
    CONTRACT_STATUS_GUARANTEE = 10
    CONTRACT_STATUS_CHOICES = (
        (CONTRACT_STATUS_NONE, u'未签订'),
        (CONTRACT_STATUS_ONSITE, u'协调现场'),
        (CONTRACT_STATUS_ORDER, u'设备订货'),
        (CONTRACT_STATUS_RECEIVE, u'设备到货'),
        (CONTRACT_STATUS_HIDE_OPERATION, u'隐蔽施工'),
        (CONTRACT_STATUS_HIDE_COMPLETE, u'隐蔽完成'),
        (CONTRACT_STATUS_HIDE_INSTALL, u'室外安装'),
        (CONTRACT_STATUS_DEBUG, u'调试设备'),
        (CONTRACT_STATUS_ACCEPT, u'客户验收'),
        (CONTRACT_STATUS_DELIVER, u'客户交付'),
        (CONTRACT_STATUS_GUARANTEE, u'质保中'),
    )
    contract_status = models.IntegerField(verbose_name=u'合同状态',
                                          choices=CONTRACT_STATUS_CHOICES,
                                          default=CONTRACT_STATUS_NONE, )

    description = models.TextField(verbose_name=u'描述',
                                   max_length=512,
                                   blank=True,
                                   default='',)

    designer = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 verbose_name=u'设计人',
                                 related_name='+',
                                 blank=True,
                                 null=True,)

    last_contact_date = models.DateTimeField(verbose_name=u'最近联系日期',
                                             help_text=u'沟通记录的最大日期',
                                             null=True,
                                             editable=False)

    interesting_brand_categories = models.ManyToManyField(BrandToProductCategory,
                                                          verbose_name=u'感兴趣品牌类型',
                                                          blank=True,
                                                          null=True)

    def address(self):
        try:
            return "%s-%s" % (unicode(self.building), self.house_number)
        except:
            return "新建项目"

    def __unicode__(self):
        return self.address()

    def get_owner(self):
        return self.customer.get_owner()

    class Meta:
        verbose_name = u'项目'
        unique_together = ('building', 'house_number')
        ordering = ('-updated',)


class ProjectTracking(TrackingBaseModel):

    project = models.ForeignKey(Project,
                                verbose_name=u'项目',
                                related_name='trackings')

    def __unicode__(self):
        return "%s-%s" % (unicode(self.project), self.get_contact_method_display())

    class Meta:
        verbose_name = u'沟通记录'
        ordering = ('-updated',)


@receiver(signals.post_save, sender=ProjectTracking)
def handle_projecttracking_changed(sender, **kwargs):
    tracking = kwargs['instance']
    q = ProjectTracking.objects.only('id').filter(project=tracking.project).annotate(max_contact_date=Max('contact_date'))
    Project.objects.filter(id=tracking.project.id).update(last_contact_date=q[0].max_contact_date)


class ProjectHistory(TimeBaseModel):
    project = models.ForeignKey(Project,
                                verbose_name=u'项目',
                                related_name='histories')

    status = models.IntegerField(choices=Project.CONTRACT_STATUS_CHOICES,
                                 default=Project.CONTRACT_STATUS_NONE,
                                 verbose_name=u'项目合同状态')

    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                verbose_name=u'创建人',
                                related_name='+')

    class Meta:
        verbose_name = u'项目合同状态记录'
        ordering = ('-updated',)

    def __unicode__(self):
        return "%s-%s" % (unicode(self.project), self.get_status_display())


class HouseModel(TimeBaseModel):

    building = models.ForeignKey(Building,
                                 verbose_name=u'楼盘',
                                 related_name='models')

    model = models.CharField(verbose_name=u'户型',
                             max_length=16)

    area = models.FloatField(verbose_name=u'面积(平方米)',
                             default=0)

    description = models.CharField(verbose_name=u'户型描述',
                                   max_length=32,
                                   default='')

    class Meta:
        verbose_name = u'户型信息'
        unique_together = ('building', 'model')
        ordering = ('-updated',)

    def __unicode__(self):
        return "%s-%s" % (unicode(self.model), unicode(self.building.name))
