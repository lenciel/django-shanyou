#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os

from rest_framework import serializers

logger = logging.getLogger('apps.' + os.path.basename(os.path.dirname(__file__)))


class ZeroIntegerField(serializers.IntegerField):
    def to_native(self, obj):
        return obj if obj else 0


class DefaultBooleanField(serializers.BooleanField):
    def to_native(self, obj):
        return obj if obj else False
