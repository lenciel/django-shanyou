#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
from django import forms
from apps.common.ace import AceBooleanField
from apps.common.admin.datatables import DatatablesBuilder, DatatablesIdColumn, DatatablesTextColumn, DatatablesBooleanColumn, DatatablesActionsColumn, DatatablesDateTimeColumn
from .models import Image, ClientApp, OS_TYPE_ANDROID, OS_TYPE_IOS

logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(__file__)))


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = {"image_file"}


class ClientAppForm(forms.ModelForm):

    is_force_upgrade = AceBooleanField(label=u'强制更新', required=False)

    def __init__(self, *args, **kwargs):
        super(ClientAppForm, self).__init__(*args, **kwargs)
        self.fields['os'].widget.attrs['class'] = "input-large"
        self.fields['app_url'].widget.attrs['class'] = "col-md-10 limited"
        self.fields['desc'].widget.attrs['class'] = "input-xxlarge"
        # use FileInput widget to avoid show clearable link and text
        self.fields['app_file'].widget = forms.FileInput()


    class Meta:
        model = ClientApp
        fields = ("os", "app_file", "app_url", "app_version_code", "app_version_name",
                  "is_force_upgrade", "desc")

    def clean(self):
        cleaned_data = super(ClientAppForm, self).clean()
        if cleaned_data['os'] == OS_TYPE_ANDROID:
            if not cleaned_data['app_file']:
                raise forms.ValidationError(u'请上传android应用文件')
        if cleaned_data['os'] == OS_TYPE_IOS:
            if not cleaned_data['app_url']:
                raise forms.ValidationError(u'请输入iOS应用AppStore链接')
        # keep the old image and delete it if changed at save()
        self.old_app_file = self.instance.app_file
        return cleaned_data

    def save(self, commit=True):
        model_instance = super(ClientAppForm, self).save(commit)
        if self.old_app_file and self.old_app_file != model_instance.app_file:
            os.unlink(self.old_app_file.path)
        return model_instance


class ClientAppDatatablesBuilder(DatatablesBuilder):

    id = DatatablesIdColumn()

        #fields = ("os", "app_file", "app_url", "app_version_code", "app_version_name",
        #          "is_force_upgrade", "description")

    os = DatatablesTextColumn(is_searchable=True,
                              col_width="7%")

    download_url = DatatablesTextColumn(label=u'下载',
                                        render=(lambda request, model, field_name:
                                             u"<a href='%s' target='_blank'>下载</a>" % model.download_url()))

    app_version_code = DatatablesTextColumn(is_sortable=True)

    app_version_name = DatatablesTextColumn()

    is_force_upgrade = DatatablesBooleanColumn()

    updated = DatatablesDateTimeColumn()

    _actions = DatatablesActionsColumn()

    class Meta:
        model = ClientApp
