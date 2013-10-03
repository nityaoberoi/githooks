#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import sys
from sh import git, ErrorReturnCode

from .colors import red, green, highlight
from .core import FILE_TYPES
from .plugins import Command

_HOOKS = {}


class MetaHook(type):

    def __new__(mcs, name, bases, attrs):
        newcls = type.__new__(mcs, name, bases, attrs)
        if name != 'Hook':
            if not hasattr(newcls, 'name'):
                raise TypeError("Yo, I need a class with the 'name' attr")
            _HOOKS[newcls.name] = newcls
        return newcls


class Hook(object):

    name = None

    __metaclass__ = MetaHook

    @classmethod
    def supported_hooks(cls):
        return _HOOKS

    @classmethod
    def from_name(cls, name):
        try:
            hook = _HOOKS[name]
        except KeyError:
            hook = None
        return hook

    def prepare(self):
        raise NotImplementedError


class PreCommitHook(Hook):

    name = 'pre-commit'
    result = 0

    def prepare(self):
        modified = re.compile('^[MA]\s+(?P<name>.*)$')
        self.files = []
        mod_files = git.status('--porcelain')
        for mod_file in mod_files.splitlines():
            match = modified.match(mod_file)
            if match:
                self.files.append(match.group('name'))
        print highlight('Stashing all untracked changes...')
        git.stash('--include-untracked', '--keep-index')

    def run(self):
        for file_type in FILE_TYPES:
            key = 'hooks.{}.{}'.format(self.name, file_type)
            hooks = git.config(key).strip('\\n').split(',')
            for hook in hooks:
                command = Command.from_name(hook)()
                sys.stdout.write(highlight('{}'.format(command.output)))
                sys.stdout.flush()
                try:
                    command.run(files=self.files)
                except ErrorReturnCode, e:
                    print red(' ✗')
                    print ' ', '\n  '.join([e.stderr, e.stdout])
                    self.result = 1
                    break
                else:
                    print green(' ✔ ')

            if self.result == 1:
                break

    def post_run(self):
        git.reset('--hard')
        try:
            # This hook can be called by a simple git commit --amend
            # without anything to actually get from the stash. In this
            # case, this command will break and we can safely ignore it.
            git.stash('pop', '--quiet', '--index')
        except Exception:
            pass

        sys.exit(self.result)
