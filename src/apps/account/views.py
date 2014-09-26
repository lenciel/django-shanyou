#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from django.contrib import auth

from django.contrib.auth.models import Group
from django.contrib.auth.views import password_reset
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.views.generic import RedirectView
from apps.common import exceptions
from apps.common.admin.views import NavigationHomeMixin, ModelAwareMixin, DatatablesBuilderMixin, AjaxListView,\
    AjaxDatatablesView, RequestAwareMixin, AjaxUpdateView, AjaxSimpleUpdateView, AdminRequiredMixin, HttpResponseJson, AjaxFormView
from apps.account.models import User, Department

from .forms import GroupForm, GroupDatatablesBuilder, UserDatatablesBuilder, UserForm, UserChangePasswordForm, DepartmentForm, DepartmentDatatablesBuilder


logger = logging.getLogger('apps.'+os.path.basename(os.path.dirname(__file__)))


def login_view(request):
    result = exceptions.build_success_response_result()

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        next = request.GET.get('next', '')
        user = auth.authenticate(username=username, password=password)
        if user:
            if not user.is_staff:
                # don't allow customer login to admin
                return redirect('website:home')
            if user.is_active:
                logger.info('Authenticate success for user ' + username)
                # Correct password, and the user is marked "active"
                auth.login(request, user)
                if next:
                    return redirect(next)
                else:
                    return redirect('/admin')
        else:
            logger.info('Authenticate failed for user ' + username)
            result = exceptions.build_response_result(exceptions.ERROR_CODE_AUTH_FAILED_INVALID_USERNAME_OR_PASSWORD)

    return render_to_response('account/login.html',
                              locals(),
                              context_instance=RequestContext(request))


class LogoutView(RedirectView):
    def get_redirect_url(self, **kwargs):
        auth.logout(self.request)
        return reverse('admin:account:login', args=kwargs)


class GroupListDatatablesView(NavigationHomeMixin, ModelAwareMixin, DatatablesBuilderMixin, AdminRequiredMixin, AjaxDatatablesView):
    model = Group
    app_label = 'account'
    queryset = Group.objects.prefetch_related().order_by('name')
    datatables_builder_class = GroupDatatablesBuilder


class GroupFormView(RequestAwareMixin, ModelAwareMixin, AdminRequiredMixin, AjaxFormView):
    model = Group
    form_class = GroupForm
    app_label = 'account'


class GroupDeleteView(AdminRequiredMixin, AjaxSimpleUpdateView):
    model = Group
    app_label = 'account'

    def update(self, group):
        group.delete()


class UserListDatatablesView(NavigationHomeMixin, ModelAwareMixin, DatatablesBuilderMixin, AdminRequiredMixin, AjaxDatatablesView):
    model = auth.get_user_model()
    queryset = auth.get_user_model().staffs.prefetch_related().order_by('-date_joined')
    datatables_builder_class = UserDatatablesBuilder
    model_name = 'user'


class UserFormView(RequestAwareMixin, ModelAwareMixin, AdminRequiredMixin, AjaxFormView):
    model = auth.get_user_model()
    form_class = UserForm
    model_name = 'user'
    template_name = 'account/user.form.inc.html'

    def get_context_data(self, **kwargs):
        context = super(UserFormView, self).get_context_data(**kwargs)
        if self.object:
            # only apply dummy password for the edit case.
            context['dummy_password'] = UserForm.DUMMY_PASSWORD
        return context


class UserLockView(AdminRequiredMixin, AjaxSimpleUpdateView):
    model = auth.get_user_model()

    def update(self, user):
        if self.request.user.id == user.id:
            return u"不允许自己锁定自己!"
        if user.is_superuser:
            return u"不允许锁定超级用户!"
        if user.is_rubbish():
            return u"不允许锁定*公海*!"
        user.is_active = False
        user.save()


class UserUnlockView(AdminRequiredMixin, AjaxSimpleUpdateView):
    model = auth.get_user_model()

    def update(self, user):
        user.is_active = True
        user.save()


class UserChangePasswordView(ModelAwareMixin, RequestAwareMixin, AjaxUpdateView):
    model = auth.get_user_model()
    form_class = UserChangePasswordForm
    model_name = 'user'
    template_name = 'account/user.changepassword.inc.html'
    form_action_url_name = 'admin:account:change_password'

    def get_context_data(self, **kwargs):
        data = super(UserChangePasswordView, self).get_context_data(**kwargs)
        data['page_title'] = u'修改密码'
        return data


class UserResetPasswordView(AdminRequiredMixin, AjaxSimpleUpdateView):
    model = auth.get_user_model()

    def post(self, request, *args, **kwargs):
        email = request.POST['email']
        target_user = User.objects.get(email=email)
        if not target_user.is_staff:
            kwargs.update(post_reset_redirect='/to_email_confirm')
            kwargs.update(template_name='customer/website/customer.reset.password.form.html')
            kwargs.update(email_template_name='customer/website/customer.reset.password.email.html')
            kwargs.update(subject_template_name='customer/website/customer.reset.password.subject.txt')
        password_reset(request=request, **kwargs)
        return HttpResponseJson(exceptions.build_success_response_result(), request)


class DepartmentListDatatablesView(NavigationHomeMixin, ModelAwareMixin, DatatablesBuilderMixin, AdminRequiredMixin, AjaxDatatablesView):
    model = Department
    app_label = 'account'
    queryset = Department.objects.prefetch_related().order_by('name')
    datatables_builder_class = DepartmentDatatablesBuilder


class DepartmentFormView(RequestAwareMixin, ModelAwareMixin, AdminRequiredMixin, AjaxFormView):
    model = Department
    form_class = DepartmentForm
    app_label = 'account'


class DepartmentDeleteView(AdminRequiredMixin, AjaxSimpleUpdateView):
    model = Department
    app_label = 'account'

    def update(self, department):
        if department.is_removable():
            department.delete()
        else:
            return u'部门下尚有员工，无法删除。'


