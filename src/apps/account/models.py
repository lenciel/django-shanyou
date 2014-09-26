#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
from django.contrib.auth.models import UserManager, AbstractBaseUser, PermissionsMixin
from django.db.models import Model
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django.db import models
from django.contrib import auth

logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(__file__)))


class StaffManager(models.Manager):
    def get_query_set(self):
        return super(StaffManager, self).get_query_set().filter(is_staff=True).exclude(id=User.USER_ID_ADMIN)

    def active_objects(self):
        return self.get_query_set().filter(is_active=True)


class DeferUserManager(UserManager):
    def get_query_set(self):
        # defer some infrequently used fields.
        return super(DeferUserManager, self).get_query_set().defer('gender', 'phone', 'qq', 'wechat', 'email', 'password',
                                                                   'ext_number','gender', 'date_joined', 'last_login')


class User(AbstractBaseUser, PermissionsMixin):
    USER_ID_ADMIN = 1
    USER_ID_RUBBISH = 2

    name = models.CharField(verbose_name=u'用户名',
                            max_length=30,
                            unique=True)

    email = models.EmailField(verbose_name=u'邮箱',
                              unique=True)

    real_name = models.CharField(verbose_name=u'姓名',
                                 default="",
                                 blank=True,
                                 max_length=30)

    phone = models.CharField(max_length=32,
                             verbose_name=u'电话',
                             unique=True)

    qq = models.CharField(max_length=32,
                          verbose_name=u'QQ号',
                          unique=True)

    wechat = models.CharField(max_length=32,
                              verbose_name=u'微信号',
                              unique=True)

    ext_number = models.CharField(max_length=32,
                                  verbose_name=u'分机号',
                                  default="",
                                  blank=True)

    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'
    GENDER_CHOICES = (
        (GENDER_MALE, u'男'),
        (GENDER_FEMALE, u'女'),
    )

    gender = models.CharField(max_length=12, choices=GENDER_CHOICES,
                              default=GENDER_MALE,
                              blank=True,
                              verbose_name=u'性别')

    is_staff = models.BooleanField(_('staff status'),
                                   default=False,
                                   help_text=_('Designates whether the user can log into this admin '
                                               'site.'))
    is_active = models.BooleanField(_('active'),
                                    default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))

    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    department = models.ForeignKey('Department',
                                   null=True,
                                   blank=True,
                                   default=None,
                                   related_name='users',
                                   verbose_name=u'部门')

    accessible_users = models.ManyToManyField('self',
                                              null=True,
                                              blank=True,
                                              symmetrical=False,
                                              verbose_name=u'下属',
                                              related_name='+', )

    objects = DeferUserManager()
    staffs = StaffManager()

    USERNAME_FIELD = 'name'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_absolute_url(self):
        return "/users/%d/" % self.id

    def get_full_name(self):
        return self.real_name

    def get_short_name(self):
        "Returns the short name for the user."
        return self.real_name

    def is_admin(self):
        return self.id == self.USER_ID_ADMIN

    def is_rubbish(self):
        # dummy user 公海
        return self.id == self.USER_ID_RUBBISH

    def is_customer(self):
        return not self.is_staff

    def is_superior(self, user):
        return self.is_superuser or user.is_rubbish() or self.accessible_users.filter(id=user.id).count()

    def has_perm_access(self, base_model):
        return base_model.get_owner().id == self.id or self.is_superior(base_model.get_owner())

    def accessible_user_ids(self, include_rubbish_user=False):
        if self.is_superuser:
            return User.staffs.active_objects().values_list('id', flat=True)
        ids = list(self.accessible_users.values_list('id', flat=True))
        ids.append(self.id)
        if include_rubbish_user:
            ids.append(self.USER_ID_RUBBISH)
        return ids

    def __unicode__(self):
        return self.get_full_name()


class Department(Model):

    name = models.CharField(verbose_name='名称',
                            max_length=30,
                            unique=True)

    class Meta:
        verbose_name = u'部门'

    def is_removable(self):
        return not self.users.count()

    def __unicode__(self):
        return self.name


def accessible_users(master_user):
    """
    Return the a couple of users whose are accessible to master user
    Note: accessible users contain master user as well
    """
    if master_user.is_superuser:
        return auth.get_user_model().objects.only("name").filter(is_active=True)

    users = master_user.accessible_users.only("name").filter(is_active=True)

    # add master first
    ret = {master_user}
    ret |= ({user for user in users})
    return ret
