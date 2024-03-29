#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from crispy_forms.bootstrap import InlineCheckboxes
import os

from django import forms
from django.contrib import auth
from django.contrib.auth.models import Group, Permission
from apps.account.models import Department, User
from apps.common import exceptions
from apps.common.ace import AceBooleanField
from apps.common.admin.datatables import DatatablesBuilder, DatatablesIdColumn, DatatablesTextColumn, DatatablesDateTimeColumn, DatatablesBooleanColumn, DatatablesActionsColumn, \
    DatatablesColumnActionsRender, DatatablesModelChoiceColumn, DatatablesChoiceColumn
from apps.common.admin.forms import CrispyModelForm


logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(__file__)))

PERM_CODE_NAMES = [
    'change_customer',
    # 产品权限
    'change_productcategory',
]

PERM_EDIT_DEPARTMENT = 'account.change_department'


class UserForm(CrispyModelForm):
    # a dummy password to init to password editor of edit form
    DUMMY_PASSWORD = 'B5566AF90F4A'

    is_superuser = AceBooleanField(label=u'是否管理员',
                                   initial=False,
                                   required=False)

    confirm_password = forms.CharField(label=u'确认密码',
                                       widget=forms.PasswordInput(attrs={
                                            'class': "required xlarge-input",
                                            'placeholder': u'确认密码，必填项'}))

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['user_permissions'].queryset = Permission.objects.filter(codename__in=PERM_CODE_NAMES)
        self.fields['user_permissions'].widget.attrs['data-placeholder'] = "选择权限"

        self.fields['accessible_users'].queryset = auth.get_user_model().staffs.active_objects().only("real_name").exclude(id=User.USER_ID_RUBBISH)
        accessible_users_index = self.helper['accessible_users'].slice[0][0][0]
        self.helper[accessible_users_index] = InlineCheckboxes('accessible_users')
        self.fields['accessible_users'].help_text = u""

        self.fields['name'].widget.attrs['autofocus'] = "autofocus"
        self.fields['real_name'].required = True

        if "password" in self.fields:
            self.fields['password'].widget = forms.PasswordInput(
                attrs={'class': "required xlarge-input",
                       'placeholder': u'确认密码，必填项'})

    class Meta:
        model = auth.get_user_model()
        fields = ('name', "real_name", 'email', 'phone', 'qq', 'wechat', 'ext_number', 'gender',
                  'is_superuser', 'department', 'user_permissions', 'password', 'confirm_password', 'accessible_users')

    def save(self, commit=False):
        # 保存新用户的密码
        user = super(UserForm, self).save(commit)
        # it means user has changed the password if password is not dummy one
        if self.cleaned_data['password'] != self.DUMMY_PASSWORD:
            user.set_password(self.cleaned_data['password'])
        user.is_staff = True
        user.save()
        return user


class UserDatatablesBuilder(DatatablesBuilder):

    id = DatatablesIdColumn()

    department = DatatablesModelChoiceColumn(queryset=Department.objects.only("name"),
                                             is_searchable=True)

    real_name = DatatablesTextColumn(is_searchable=True)

    name = DatatablesTextColumn(is_searchable=True)

    gender = DatatablesChoiceColumn(User.GENDER_CHOICES,
                                    is_searchable=True,)

    email = DatatablesTextColumn(is_searchable=True)

    qq = DatatablesTextColumn(is_searchable=True)

    is_active = DatatablesBooleanColumn((('', u'全部'), (1, u'激活'), (0, u'锁定')),
                                        label='状态',
                                        is_searchable=True,
                                        col_width='7%',
                                        render=(lambda request, model, field_name:
                                                u'<span class="label label-info"> 启用 </span>' if model.is_active else
                                                u'<span class="label label-warning"> 禁用 </span>'))

    is_superuser = DatatablesBooleanColumn(label=u'管理员',
                                           col_width='5%',
                                           is_searchable=True)

    date_joined = DatatablesDateTimeColumn(label=u'创建时间')

    def actions_render(request, model, field_name):
        if model.is_active:
            actions = [{'is_link': False, 'name': 'lock', 'text': u'锁定',
                        'icon': 'icon-lock', 'url_name': 'admin:account:user_lock'},]
        else:
            actions = [{'is_link': False, 'name': 'unlock', 'text': u'解锁',
                        'icon': 'icon-unlock', 'url_name': 'admin:account:user_unlock'}]
        actions.append({'is_link': True, 'name': 'edit', 'text': u'编辑',
                        'icon': 'icon-edit', 'url_name': 'admin:account:user_edit'})
        return DatatablesColumnActionsRender(actions).render(request, model, field_name)

    _actions = DatatablesActionsColumn(render=actions_render)

    class Meta:
        model = User


class GroupForm(CrispyModelForm):

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.fields['permissions'].queryset = Permission.objects.filter(codename__in=PERM_CODE_NAMES)

    class Meta:
        model = Group
        fields = ('name', 'permissions')


class GroupDatatablesBuilder(DatatablesBuilder):

    id = DatatablesIdColumn()

    name = DatatablesTextColumn(is_searchable=True)

    class Meta:
        model = Group


class UserChangePasswordForm(CrispyModelForm):
    old_password = forms.CharField(label=u'旧密码', required=True)

    new_password = forms.CharField(label=u'新密码', required=True)

    confirm_password = forms.CharField(label=u'确认密码', required=True)

    def __init__(self, *args, **kwargs):
        super(UserChangePasswordForm, self).__init__(*args, **kwargs)
        self.fields['old_password'].widget = forms.PasswordInput(
            attrs={'class': "required", 'placeholder': u'旧密码，必填项'})
        self.fields['new_password'].widget = forms.PasswordInput(
            attrs={'class': "required", 'placeholder': u'新密码，必填项'})
        self.fields['confirm_password'].widget = forms.PasswordInput(
            attrs={'class': "required", 'placeholder': u'再次输入密码，必填项'})

    def clean(self):
        cleaned_data = super(UserChangePasswordForm, self).clean()
        request_user = self.initial['request'].user
        result = None
        if cleaned_data['new_password'] != cleaned_data['confirm_password']:
            result = exceptions.build_response_result(exceptions.ERROR_CODE_NEW_PASSWORD_NOT_MATCH)
        else:
            if self.instance.id == request_user.id:
                # 修改自己的密码前需要先认证
                user = auth.authenticate(username=request_user.name,
                                         password=cleaned_data['old_password'])
                if not user:
                    result = exceptions.build_response_result(exceptions.ERROR_CODE_AUTH_FAILED_INVALID_USERNAME_OR_PASSWORD)
            elif request_user.is_superuser:
                pass
            else:
                result = exceptions.build_response_result(exceptions.ERROR_CODE_PERMISSION_DENY)
        if result:
            raise forms.ValidationError(result['errmsg'])
        return cleaned_data

    def save(self, commit=False):
        user = super(UserChangePasswordForm, self).save(commit)
        user.set_password(self.cleaned_data['new_password'])
        user.save()
        return user

    class Meta:
        model = auth.get_user_model()
        fields = ('old_password', 'new_password', 'confirm_password')


class DepartmentForm(CrispyModelForm):

    class Meta:
        model = Department
        fields = ('name',)


class DepartmentDatatablesBuilder(DatatablesBuilder):

    id = DatatablesIdColumn()

    name = DatatablesTextColumn(is_searchable=True)

    def actions_render(request, model, field_name):
        actions = [{'is_link': True, 'name': 'edit', 'text': u'编辑', 'icon': 'icon-edit'},]
        return DatatablesColumnActionsRender(actions=actions, action_permission=PERM_EDIT_DEPARTMENT).render(request, model, field_name)

    _actions = DatatablesActionsColumn(render=actions_render)

    class Meta:
        model = Department
