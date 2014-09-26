#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from django.views.generic.base import TemplateView
import os

logger = logging.getLogger('apps.'+os.path.basename(os.path.dirname(__file__)))


class SnapshotView(TemplateView):
    template_name = 'introduction/index.html'
