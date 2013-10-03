#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from .hooks import Hook


class Dispatcher(object):

    def __init__(self, script_name):
        self.hook_type = os.path.basename(script_name)

    def run(self):
        hook = Hook.from_name(self.hook_type)()
        hook.prepare()
        hook.run()
        hook.post_run()
