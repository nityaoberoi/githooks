#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .exceptions import CommandException

_COMMANDS = {}


class MetaCommand(type):

    def __new__(mcs, name, bases, attrs):
        newcls = type.__new__(mcs, name, bases, attrs)
        if name != 'Command':
            if not hasattr(newcls, 'name'):
                raise TypeError("Yo, I need a class with the 'name' attr")
            _COMMANDS[newcls.name] = newcls

        return newcls


class Command(object):

    ignore_files = None
    match_files = None
    name = None
    output = None

    __metaclass__ = MetaCommand

    @classmethod
    def from_name(cls, name):
        return _COMMANDS[name]

    def run(self, **kwargs):
        raise NotImplementedError

    def should_check_file(self, file_name):
        return ((not self.match_files or self.matches_file(file_name, self.match_files))
            and (not self.ignore_files or not self.matches_file(file_name, self.ignore_files)))


class Pep8(Command):

    name = 'pep8'
    output = 'Running pep8...'
    match_files = '.*\.py$'
    ignore_files = None
    # constraints = [
    #     FileTypeConstraint('*.py'),
    #     Confilcts('pre-commit'),
    # ]

    def run(self, files=None):
        from sh import pep8
        for _file in files:
            rc = pep8('-r', '--ignore=E501,E502,W293,E121,E123,E124,E125,E126,E127,E128', _file)
            if rc.exit_code:
                raise CommandException(rc.err)


class UnitTest(Command):

    name = 'unittest'
    output = 'Running python unit tests...'

    def run(self, files=None):
        pass
        # command = 'python manage.py test --verbosity=0 --unit --settings=settings.isolated_tests'


class ModelValidation(Command):

    name = 'model-validation'
    output = 'Running django model validation...'

    def run(self):
        pass