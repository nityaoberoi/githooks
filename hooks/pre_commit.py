#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import subprocess


class PreCommitHook(object):






    def check_files(self, files, check):

        check_files = filter(lambda name: self.should_check_file(check, name), files)

        if check_files:
            if check.get('ignore_noqa_lines'):
                check['command'] += ' | grep -vi "#*noqa"'

            file_names = '" "'.join(check_files)
            relevant_module_infos = get_relevant_module_infos(check_files)

            extra_info = {}
            required_infos = set(re.findall(r'[{](\w+)[}]', check['command']))

            command_requires_extra_info = not bool(required_infos.difference(possible_module_infos))

            if command_requires_extra_info:
                if not relevant_module_infos:
                    return 0  # the current command requires
                              # relevant_module_infos but none is
                              # available, let's forget this one

                extra_info = relevant_module_infos[0]
                output_label = highlight(check['output'].format(**extra_info))

            else:
                output_label = highlight(check['output'])

            sys.stdout.write(output_label)
            sys.stdout.flush()

            command = check['command'].format(file_name=file_names, filenames=file_names, **extra_info)
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            out, err = process.communicate()

            if out or err:
                print self.error(' ✗')
                print ' ', '\n  '.join(out.splitlines())

                if err:
                    print err

                if 'error_message' in check:
                    print
                    print highlight(check['error_message'])
                    print

                return 1

            print ok(' ✔ ')

        return 0

    def should_check_file(self, check, file_name):
        return (not 'match_files' in check or matches_file(file_name, check['match_files']))\
            and (not 'ignore_files' in check or not matches_file(file_name, check['ignore_files']))


class Pep8Hook(PreCommitHook):

    shell_name='pep8'
