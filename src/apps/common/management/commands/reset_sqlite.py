#!/usr/bin/env python
# -*- coding: utf-8 -*-
import glob
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand, call_command
import os


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-t', '--test',
                    action='store_true',
                    dest='test',
                    default=False,
                    help='load the test data'),
    )
    """
    A simple command to delete the local sqlite db and recreate it with "syncdb"
    run it as below:
        ./manage.py reset_sqlite --settings=settings.local
    """
    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != "settings.local":
            raise BaseException(u'必须在local下运行!')
        db_path = settings.DATABASES['default']['NAME']
        if os.path.exists(db_path):
            os.unlink(db_path)

        # delete old test stuffs
        old_files = glob.glob(os.path.join(settings.MEDIA_ROOT, settings.MEDIA_IMAGE_PREFIX)+"/*.*")
        old_files.extend(glob.glob(os.path.join(settings.MEDIA_ROOT, settings.MEDIA_CONTENT_PREFIX)+"/*.*"))
        for f in old_files:
            os.unlink(f)

        call_command("syncdb", migrate=True, interactive=False, settings=settings.SETTINGS_MODULE, traceback=True, verbosity=0)
        fixtures = []
        if options['test']:
            for apps in settings.PROJECT_APPS:
                short_name = apps.split(".")[-1]
                fixtures += ["test_%s_data.json" % short_name]
        call_command("loaddata", *fixtures, settings=settings.SETTINGS_MODULE, traceback=True, verbosity=0)
