#!/usr/bin/env python
# -*- coding: utf-8 -*-
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from south.models import MigrationHistory


class Command(BaseCommand):
    """
    Show the installed apps. It only support show the unmigration apps only.
    """
    help = 'Show the installed apps.'

    option_list = BaseCommand.option_list + (
        make_option('-u', '--unmigration_only',
                    action='store_true',
                    dest='unmigration_only',
                    default=False,
                    help='only return unmigration apps'),
        make_option('-m', '--migrated_only',
                    action='store_true',
                    dest='migrated_only',
                    default=False,
                    help='only return migrated apps'),
    )

    def handle(self, *args, **options):
        all_apps = settings.INSTALLED_APPS
        if options['unmigration_only']:
            apps = self.get_unmigration_apps(all_apps)
        elif options['migrated_only']:
            apps = self.get_migrated_apps(all_apps)
        else:
            apps = all_apps

        print ' '.join(apps)

    def get_unmigration_apps(self, all_apps):
        new_apps = []
        migrated_apps = MigrationHistory.objects.all()
        for app in all_apps:
            new_app = app
            for history in migrated_apps:
                if app.endswith(history.app_name):
                    new_app = ""
                    break
            if new_app:
                new_apps.append(new_app)
        return new_apps

    def get_migrated_apps(self, all_apps):
        unmigrated_apps = self.get_unmigration_apps(all_apps)
        return list(set(all_apps) - set(unmigrated_apps))



