#!/usr/bin/env python
# -*- coding: utf-8 -*-
import hashlib
import json
import logging
from optparse import make_option
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
import os
import requests.certs

HERE = os.path.dirname(__file__)
logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(HERE)) + '.' + os.path.basename(HERE))

SNAPSHOT_JSON_FILE = "snapshots.json"
DEPENDENCY_STATIC_DIRS = ["website/fonts", "website/img"]


class Command(BaseCommand):
    """
    take the snapshot of apps that support snapshot protocol.
    it collect the dependency files and put them together. Finally, it make snapshot standalone.
    """
    option_list = BaseCommand.option_list + (
        make_option('-p', '--port',
                    action='store',
                    dest='port',
                    default=8018,
                    help='website port'),
        make_option('-s', '--server',
                    action='store',
                    dest='server',
                    default='127.0.0.1',
                    help='website server'),
        make_option('-d', '--output_dir',
                    action='store',
                    dest='output_dir',
                    default=os.path.join(settings.MEDIA_ROOT, settings.MEDIA_APP_SNAPSHOT),
                    help='dir which app file should be snapshot'),
    )

    def handle(self, *args, **options):
        self.output_dir = options['output_dir']
        self.server = options['server']
        self.port = options['port']

        snapshot_apps = []
        for app in settings.PROJECT_APPS:
            app = app.replace("apps.", "").lower()
            app_dir = os.path.join(self.output_dir, app)
            html = self.collect_snapshot(app, app_dir)
            if html:
                self.collect_files_in_compress_cache(html, app_dir)
                self.collect_files_in_static(app, app_dir)
                self.zip_app_snapshot(app_dir)
                snapshot_apps.append({"app": app,
                                      "sha1": self.get_file_sha1(app_dir + ".zip"),
                                      "url": "/media/snapshots/%s.zip" % app})
        fp = open(os.path.join(self.output_dir, SNAPSHOT_JSON_FILE), "w")
        json.dump(snapshot_apps, fp)

    def collect_snapshot(self, app, app_dir):
        url = 'http://%s:%s/%s/snapshot/' % (self.server, self.port, app)
        logger.debug("access " + url + " to get content")
        r = requests.get(url)
        if r.status_code == 200:
            if os.path.exists(app_dir):
                shutil.rmtree(app_dir)
            os.mkdir(app_dir)
            html = self.handle_absolute_url(r.text)
            with open(os.path.join(app_dir, "index.html"), 'w') as f:
                f.write(html)
            return html
        else:
            logger.debug("ignore %s due to not support snapshot protocol " % app)

    def handle_absolute_url(self, html):
        """
        convert absolute resource path to relative one.
        """
        html = html.replace('/static/', 'static/')
        html = html.replace('/media/', 'media/')
        return html

    def collect_files_in_compress_cache(self, snapshot_html, app_dir):
        """
        midleware "compress" will compress and mix the javascript and stylesheet file into "/static/cache/..."
        So collect these kind of file into app snapshot.
        """
        import re
        #"<link rel=\"stylesheet\" href=\"/static/CACHE/css/3998106e131f.css\" type=\"text/css\" />",
        #"2084c7050a2084a1d9728d31155a14c0": "<script type=\"text/javascript\" src=\"/static/CACHE/js/4f485046b8ab.js\"></script>"
        re_list = (re.compile(r'src="static/(CACHE/js/\w+\.js)"'),
                   re.compile(r'href="static/(CACHE/css/\w+\.css)"'))
        for r in re_list:
            match = r.search(snapshot_html)
            if match:
                src_file = os.path.join(settings.STATIC_ROOT, match.group(1))
                dest_file = os.path.join(app_dir, 'static', match.group(1))
                logger.debug("copy cache file form %s to %s" % (src_file, dest_file))
                os.makedirs(os.path.dirname(dest_file))
                shutil.copy(src_file, dest_file)

    def collect_files_in_static(self, app, copy_to_dir):
        # always collect the files under website exclude admin
        dependency_dirs = list(DEPENDENCY_STATIC_DIRS)
        dependency_dirs.append(app)
        for dependency_dir in dependency_dirs:
            full_source_dir = os.path.join(settings.STATIC_ROOT, dependency_dir)
            logger.debug(full_source_dir + "   " + copy_to_dir)
            if os.path.exists(full_source_dir):
                shutil.copytree(full_source_dir, os.path.join(copy_to_dir, 'static', os.path.basename(full_source_dir)))

    def zip_app_snapshot(self, app_dir):
        basename = os.path.basename(app_dir)
        rootdir = os.path.dirname(app_dir)
        shutil.make_archive(os.path.join(rootdir, basename), "zip", app_dir)

    def get_file_sha1(self, path):
        """
        calculate file's sha1.
        """
        with open(path, "r") as f:
            sha = hashlib.sha1()
            while True:
                data = f.read(512 * 1024)
                if data:
                    sha.update(data)
                else:
                    break
            return sha.hexdigest()
