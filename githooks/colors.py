#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def _wrap_text_with(color):

    def inner(text):
        return '\033[1;{}m{}\033[0m'.format(color, text)
    return inner

green = _wrap_text_with('32')
red = _wrap_text_with('31')
highlight = _wrap_text_with('37')
