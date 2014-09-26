#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
from django.conf import settings
from django.db import models
from apps.common.models import TimeBaseModel
from utils import random

logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(__file__)))


def unique_image_name(instance, filename):
    try:
        ext = os.path.splitext(filename)[1].lstrip('.')
    except BaseException:
        ext = "jpg"
    return '%s/%s' % (settings.MEDIA_IMAGE_PREFIX, random.gen_uuid_filename(ext))


class ImageManager(models.Manager):

    def get_all_for_names(self, image_names):
        return self.get_query_set().filter(image_file__in=['%s/%s' % (settings.MEDIA_IMAGE_PREFIX, name) for name in image_names])


class Image(models.Model):
    """
    图片链接. 只允许添加和删除, 不允许修改. 修改的图片会创建全新的一条记录.
    """

    image_file = models.ImageField(upload_to=unique_image_name,
                                   db_index=True,
                                   verbose_name=u'图片',
                                   width_field='width',
                                   height_field='height')

    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name=u"创建日期")

    width = models.PositiveIntegerField(verbose_name='图片宽度',
                                        null=True,
                                        blank=True,
                                        default=0)
    height = models.PositiveIntegerField(verbose_name='图片长度',
                                         null=True,
                                         blank=True,
                                         default=0)

    objects = ImageManager()

    def url(self):
        return self.image_file.url

    def __unicode__(self):
        return self.url()

    class Meta:
        verbose_name = u'图片'
        verbose_name_plural = verbose_name


def unique_apk_name(instance, filename):
    return '%s/Appfac-%s' % (settings.MEDIA_APP_PREFIX, random.gen_timestamp_filename('apk'))


OS_TYPE_ANDROID = 0
OS_TYPE_IOS = 1
OS_TYPES = (
    (OS_TYPE_ANDROID, "Android"),
    (OS_TYPE_IOS, "iOS"),
)


class ClientAppManager(models.Manager):
    class DummyClientApp:
        def __init__(self):
            self.app_version_code = -1
            self.app_version_name = ""
            self.is_force_upgrade = False

        def download_url(self):
            return ""

    def get_latest_android_app(self):
        try:
            return self.active_queryset().filter(os=OS_TYPE_ANDROID).latest()
        except BaseException:
            return ClientAppManager.DummyClientApp()

    def get_latest_ios_app(self):
        try:
            return self.active_queryset().filter(os=OS_TYPE_IOS).latest()
        except BaseException:
            return ClientAppManager.DummyClientApp()

    def active_queryset(self):
        return self.get_query_set().filter(is_active=True)


class ClientApp(TimeBaseModel):
    """
    客户端版本.
    """
    os = models.IntegerField(verbose_name=u'操作系统',
                             default=OS_TYPE_ANDROID,
                             choices=OS_TYPES)

    # 如果操作系统是android, 升级文件host在应用工厂服务器.
    # app_file 只针对android客户端
    app_file = models.FileField(upload_to=unique_apk_name,
                                null=True,
                                blank=True,
                                verbose_name='App安装文件')
    # app_url 只针对iOS客户端
    app_url = models.URLField(null=True,
                              blank=True,
                              default="",
                              verbose_name='AppStore链接')

    app_version_code = models.PositiveIntegerField(default=0,
                                                   verbose_name=u"客户端版本号")
    app_version_name = models.CharField(max_length=32,
                                        default='',
                                        verbose_name=u"客户端版本名称")

    is_force_upgrade = models.BooleanField(default=False,
                                           blank=True,
                                           verbose_name=u"是否强制更新")

    desc = models.TextField(max_length=256,
                            blank=True,
                            default="",
                            verbose_name=u"描述")

    is_active = models.BooleanField(default=True,
                                    verbose_name=u'是否激活')

    objects = ClientAppManager()

    def download_url(self):
        if self.app_url:
            return self.app_url
        # TODO: prefixed the website to url
        # return urlparse.urljoin(website, self.app_file.url)
        return self.app_file.url

    def delete(self, using=None):
        if self.app_file:
            os.unlink(self.app_file.path)
        super(ClientApp, self).delete(using=using)

    class Meta:
        ordering = ('-app_version_code',)
        get_latest_by = "app_version_code"
        verbose_name = u'客户端应用'
        verbose_name_plural = verbose_name

