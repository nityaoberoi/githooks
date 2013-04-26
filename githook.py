#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import shlex
import subprocess
import sys


def wrap_text_with(color):
    return lambda msg: '{}{}{}'.format(color, msg, NC)

HIGHLIGHT = '\033[1;37m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'
NC = '\033[0m'

ok = wrap_text_with(GREEN)
error = wrap_text_with(RED)
highlight = wrap_text_with(HIGHLIGHT)

CHECKS = [
    {
        'output': 'Checking for ipdbs and pdbs...',
        'command': 'grep -EHIn "import i?pdb" "{file_name}"',
        'match_files': ['.*\.py$'],
        'ignore_noqa_lines': True,
    },
    {
        'output': 'Checking for print statements...',
        'command': 'grep -HIn "print \|print(" "{file_name}"',
        'match_files': ['.*\.py$'],
        'ignore_files': ['.*migrations.*', '.*management/commands.*', '.*manage.py$',
            '^scripts/.*', '^gists/.*', '^terrain/.*', '^fabfile.*', '.*/xenia/.*', '^conf/.*',
            '^apps/deal/tests/functional/data_for_test_tag_classifier.py$',
            '^apps/reader/tests/fixtures/.*'],
        'ignore_noqa_lines': True,
    },
    {
        'output': 'Checking for "import settings"...',
        'command': 'grep -HIn "^import settings" "{file_name}"',
        'match_files': ['.*\.py$'],
    },
    {
        'output': 'Checking for unhandled merges...',
        'command': 'grep -EHIn \'^(([<>]{{7}}\s.+)|(={{7}}))$\' "{file_name}"',
    },
    {
        'output': 'Checking for "debugger" inside js and html files...',
        'command': 'grep -Hn "debugger" "{file_name}"',
        'match_files': ['(?:.*/yipit/.*\.js$|.*\.html$)'],
        'ignore_files': ['.*/xenia/.*'],
    },
    {
        # focus rocket is a nice feature from busterjs
        # but should never be committed since it
        # limits the tests that are going to run
        'output': 'Checking for "=>" inside js test files...',
        'command': 'grep -Hn "=>" "{file_name}"',
        'match_files': ['^test-client/.*-test\.js$'],
    },
    {
        'output': 'Checking for `from __future__ import unicode_literals`',
        'command': 'grep -L "from __future__ import unicode_literals" "{file_name}"',
        'match_files': ['.*\.py$'],
        'ignore_files': ['.*migrations.*'],
    },
    {
        'output': 'Checking for `# -*- coding: utf-8 -*-`',
        'command': 'grep -L "coding: utf-8" "{file_name}"',
        'match_files': ['.*\.py$'],
    },
    {
        'output': 'Running pyflakes...',
        'command': 'yipitflakes "{file_name}"',
        'match_files': ['.*\.py$'],
        'ignore_files': ['^settings/.*', '^gists/.*', '.*migrations.*',
            '^terrain/.*', '^scripts/.*', '^conf/.*', 'apps/util/shell_builtins.py'],
    },
    {
        'output': 'Running pep8...',
        'command': 'pep8 -r --ignore=E501,E502,W293,E121,E123,E124,E125,E126,E127,E128 "{file_name}"',
        'match_files': ['.*\.py$'],
        'ignore_files': ['.*migrations.*', '^gists/.*', '^conf/.*',
            '^apps/deal/tests/functional/data_for_test_tag_classifier.py$'],
    },
    {
       'output': 'Running jshint...',
       # By default, jshint prints 'Lint Free!' upon success. We want to filter this out.
       'command': 'jshint "{file_name}" --config conf/jshint.json | grep -v "Lint Free!"',
       # filtering for files in the js/yipit directory
       'match_files': ['.*yipit/.*\.js$'],
    },
    {
        'output': 'Checking for "console.log" inside js and html files...',
        'command': 'grep -Hn "console.log" "{file_name}"',
        'match_files': ['(?:.*/yipit/.*\.js$|.*\.html$)'],
        'ignore_files': ['.*/xenia/.*'],
    },
    {
        # to see the complete list of tranformations/fixes:
        # run `2to3 -l` OR
        # see the complete list with description here: http://docs.python.org/2/library/2to3.html
        'output': 'Running 2to3...',
        'command': ('2to3 -f xreadlines -f types -f tuple_params -f throw -f sys_exc '
            '-f set_literal -f renames -f raw_input -f raise -f paren '
            '-f operator -f ne -f methodattrs -f long -f isinstance -f intern -f input '
            '-f import -f imports2 -f imports2 -f idioms -f getcwdu -f funcattrs -f exitfunc '
            '-f execfile -f exec -f except -f buffer -f apply -f numliterals '
            '"{file_name}" 2> /dev/null'),
        'match_files': ['.*\.py$'],
        'error_message': (
            'You probably have a code that will generate problems with python 3.\n'
            'Take a look at http://packages.python.org/six/ to see a python 2 and 3 compatible way or\n'
            'if the error relates to urllib, try to use requests: http://docs.python-requests.org/en/latest/\n'
            'INFO: don\'t take the diff as an absolute truth.\n'
            'INFO: If you don\'t agree with the check, send an email to coders.\n'
            'More info:\n'
            '* http://docs.python.org/3/library/2to3.html\n'
            '* http://docs.pythonsprints.com/python3_porting/py-porting.html\n'
            '* http://docs.python.org/release/3.0/whatsnew/3.0.html'
        )
    },
]

modified = re.compile('^[MA]\s+(?P<name>.*)$')


def matches_file(file_name, match_files):
    return any(re.compile(match_file).match(file_name) for match_file in match_files)


def should_check_file(check, file_name):
    return (not 'match_files' in check or matches_file(file_name, check['match_files']))\
        and (not 'ignore_files' in check or not matches_file(file_name, check['ignore_files']))


def check_files(files, check):
    check_files = [file_name for file_name in files if should_check_file(check, file_name)]

    if check_files:
        sys.stdout.write(highlight(check['output']))
        sys.stdout.flush()

        if check.get('ignore_noqa_lines'):
            check['command'] += ' | grep -vi "#*noqa"'

        file_names = '" "'.join(check_files)
        command = check['command'].format(file_name=file_names)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = process.communicate()

        if out or err:
            print error(' ✗')
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


def run(test_name, command):

    sys.stdout.write(highlight('Running {}...'.format(test_name)))
    sys.stdout.flush()

    try:
        subprocess.check_output(shlex.split(command), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print error(' ✗')
        print e.output
        raise SystemExit(e.returncode)
    else:
        print ok(' ✔ ')


def check_call(command):
    subprocess.check_call(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def get_files(all_files):
    files = []
    if all_files:
        files = subprocess.check_output(shlex.split('git ls-files --full-name')).strip().split('\n')
    else:
        out = subprocess.check_output(shlex.split('git status --porcelain'))
        for line in out.splitlines():
            match = modified.match(line)
            if match:
                files.append(match.group('name'))

    return files


def main(all_files):

    files = get_files(all_files)

    if not all_files:
        # Stash any changes to the working tree that are not going to be committed
        print highlight('Git stashing untracked changes...')
        check_call('git stash --include-untracked --keep-index')

    any_changes_on_files_ending_with = lambda ext: any([f.endswith(ext) for f in files])

    try:

        check_call('find . -name "*.pyc" -delete')

        if any_changes_on_files_ending_with('.py'):
            run('python unit tests', 'python manage.py test --verbosity=0 --unit --settings=settings.isolated_tests')
            run('django model validation', 'python manage.py validate')

        if any_changes_on_files_ending_with('.js'):
            run('javascript tests', './scripts/bin/testjs')

        if any_changes_on_files_ending_with('.scss'):
            run('sass compilation', 'y compass-compile')

        result = 0

        for check in CHECKS:
            result += check_files(files, check)
            if result and not all_files:
                break

    finally:

        if not all_files:
            # Unstash changes to the working tree that we had stashed
            check_call('git reset --hard')
            try:
                # This hook can be called by a simple git commit --amend
                # without anything to actually get from the stash. In this
                # case, this command will break and we can safely ignore it.
                check_call('git stash pop --quiet --index')
            except subprocess.CalledProcessError:
                pass

    sys.exit(result)


if __name__ == '__main__':
    all_files = False
    if len(sys.argv) > 1 and sys.argv[1] == '--all-files':
        all_files = True

    main(all_files)
