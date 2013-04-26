Plugin system for githooks

git hook init (--exclude) postcommit
git hook list (--installed/--available)
git hook register (--exclude, --include)
git hook unregister


*********************************************************
precommit.py

from githook-plugins import (
    Pep8Hook,
    JsLintHook
    UnitTestHook
)

hooks = [Pep8Hook, JsLintHook, UnitTestHook]

def run_hooks():
    for hook in hooks:
        hook.run()

*********************************************************

from hooks import Dispatcher
Dispatcher(sys.argv[0]).run()

Dispatch(pre-commit).run()

*********************************************************

register hoooks in config files:

[hooks_pre-commit]
    enabled = 'pep8,pylint'

*********************************************************