#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import logging
import os
from sh import (
    git,
    ErrorReturnCode_1,
    ErrorReturnCode_128
)
import sys


SUPPORTED_HOOKS = ['pre-commit']
FILE_TYPES = ['python', 'js', 'html']
FILE_TYPE_HOOKS = {
    'python': {'pre-commit': 'unittest,pdb,print,settings,utf8,2to3'},
    'js': {'pre-commit': 'busterjs,jshint,debugger'},
    'html': {'pre-commit': 'debugger'},
    'general': {'pre-commit': 'unhandled-merge'}
}
path_to_the_script = os.path.abspath(os.path.join(os.path.dirname(__file__), 'default_hook.py'))


def run_init(*args, **kwargs):

    # initialize the git repository if not already done
    try:
        git("rev-parse", "--dir-list")
    except ErrorReturnCode_128:
        git("init")

    exclude = kwargs.get('exclude')
    hooks_added = []

    for hook in SUPPORTED_HOOKS:
        if exclude and hook not in exclude or not exclude:
            try:
                os.symlink(path_to_the_script, '.git/hooks/{}'.format(hook))
            except OSError, e:
                if e.errno == 17:
                    logging.info('Already initialized')

            # create a temporary hook key/val
            key = 'hooks.{hook_type}.placeholder'.format(hook_type=hook)
            val = 'true'
            try:
                git.config('--get', key)
            except ErrorReturnCode_1:
                git.config('--add', key, val)

        hooks_added.append(hook)

    print "Successfully initialized hooks: {}".format(hooks_added)


def run_list(*args, **kwargs):
    pass


def run_register(*args, **kwargs):
    # TODO: Check that init has been run

    for file_type in FILE_TYPES:
        if query_yes_no('Do you wish to install hooks for {} files?'.format(file_type)):
            install_hooks(file_type)


# copied from: http://stackoverflow.com/questions/3041986/python-command-line-yes-no-input
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")


def install_hooks(file_type):
    """
    This is a fake install.
    All it does is write the list of hooks that
    need to be run to your git config file
    """
    hooks = FILE_TYPE_HOOKS[file_type]

    for hook in hooks.keys():
        try:
            base_key = 'hooks.{hook_type}'.format(hook_type=hook)
            key = '{base_key}.{key_name}'.format(base_key=base_key, key_name='placeholder')
            git.config('--get', key)
        except ErrorReturnCode_1:
            logging.info('This hook has not been installed')
            continue
        else:
            key = '{base_key}.{key_name}'.format(base_key=base_key, key_name=file_type)
            try:
                git.config('--get', key)
            except ErrorReturnCode_1:
                git.config('--add', key, hooks[hook])


COMMAND_DICT = {
    'init': run_init,
    'list': run_list,
    'register': run_register
}


def main():

    parser = argparse.ArgumentParser(description='Manage your git hooks')
    subparsers = parser.add_subparsers(dest="subcommand",
                                    title="subcommands",
                                    description="valid subcommands",
                                    help="additional help")

    sub_init = subparsers.add_parser('init', help='Initializes the hook system')
    sub_init.add_argument('-e', '--exclude', action='store', metavar='<HOOK_LIST>')

    sub_list = subparsers.add_parser('list', help='Lists hooks')
    sub_list.add_argument('-i', '--installed', action='store', metavar='<HOOK_LIST>')
    sub_list.add_argument('-a', '--available', action='store', metavar='<HOOK_LIST>')

    sub_register = subparsers.add_parser('register', help='Registers Hooks')
    sub_register.add_argument('-e', '--exclude', action='store', metavar='<HOOK_LIST>')

    parsed_args = parser.parse_args(sys.argv[1:])
    args = []
    kwargs = vars(parsed_args)

    # run the appropriate method
    COMMAND_DICT[parsed_args.subcommand](*args, **kwargs)
