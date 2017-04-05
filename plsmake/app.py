from collections import OrderedDict, deque
from contextlib import contextmanager
from functools import update_wrapper
import os
import shlex
from typing import Callable, Mapping, Sequence, Tuple

from plsmake import logger
from plsmake.env import Env
from plsmake.rule import Rule
from plsmake.utils import func_name


_current_context = None     # type: Context


class DuplicatedRule(Exception):
    pass


class NoAction(Exception):
    pass


class ActionNoResult(Exception):
    pass


class Action:
    def __init__(self, func, is_task=False):
        self.func = func
        self.is_task = is_task
        update_wrapper(self, func, updated=())

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class Context:
    def __init__(self, init_env=None):
        init_env = init_env or create_init_env()
        self.env = init_env.make_child()
        self.rule_list = OrderedDict()

    def get_rule_list(self):
        return self.rule_list

    def get_env(self):
        return self.env

    def _set_deps(self, rule_url, func):
        da = self.rule_list.setdefault(Rule(rule_url), [None, None])

        if da[0] is not None:
            logger.error('load.dup_rule', rule=rule_url)
            raise DuplicatedRule(rule_url)
        da[0] = func
        logger.info('load.read_deps', rule=rule_url, func=func.__name__)

    def _set_action(self, rule_url, func, is_task):
        da = self.rule_list.setdefault(Rule(rule_url), [None, None])

        if da[1] is not None:
            logger.error('load.dup_rule', rule=rule_url)
            raise DuplicatedRule(rule_url)
        da[1] = Action(func, is_task=is_task)
        logger.info('load.read_action', rule=rule_url, func=func.__name__, is_task=is_task)

    def deps(self, rule_url: str):
        def g(func):
            self._set_deps(rule_url, func)
            return func
        return g

    def action(self, rule_url):
        def g(func):
            self._set_action(rule_url, func, False)
            return func
        return g

    def task(self, rule_url):
        def g(func):
            self._set_action(rule_url, func, True)
            return func
        return g


def get_context() -> Context:
    return _current_context


@contextmanager
def enter_context(context: Context):
    global _current_context
    assert _current_context is None, 'Can not enter_context recursively'
    _current_context = context
    try:
        yield _current_context
    finally:
        _current_context = None


# TODO: check `make -p`
DEFAULT_ENV = dict(
    CC='cc',
    CXX='c++',
    CFLAGS=[],
    CXXFLAGS=[],
    LDFLAGS=[],
)


def create_init_env() -> Env:
    """Construct an initial environment from enviroment variable"""
    init = os.environ.copy()

    # XXX: hacks
    to_split = [key for key in init.keys() if key.endswith('FLAGS')]
    for key in to_split:
        init[key] = shlex.split(init[key])

    for key, value in DEFAULT_ENV.items():
        init.setdefault(key, value)

    return Env(init)


def load_file(filaname: str, env: Env):
    with open(filaname, 'rt') as fp:
        string = fp.read()
    return load_string(string, env)


RuleList = Mapping[Rule, Tuple[Callable, Action]]


def load_string(string: str, env: Env, exec_ns=None) -> Tuple[RuleList, Env]:
    """Return an OrderedDict of Rule -> (resolver, action) and the envrionment after exec()"""
    context = Context(init_env=env)
    with enter_context(context):
        exec(string, exec_ns or dict())
        return context.get_rule_list(), context.get_env()


ResolverResults = Mapping[str, Tuple[Sequence[str], Env, Action, Mapping]]


def resolve(target: str, rule_list: RuleList, env: Env) -> ResolverResults:
    """Return a dict of target -> (deps, env, action)"""
    result = OrderedDict()
    pending = deque([(target, env.make_child())])
    while pending:
        target, subenv = pending.popleft()  # type: Tuple[str, Env]
        assert target not in result
        depends = []
        only_action = None
        action_option = None
        log = logger.bind(target=target)

        log.info('resolve.begin')
        for rule, (resolver, action) in rule_list.items():
            matched = rule.match(target)
            if matched is not None:
                log.info('resolve.matching', rule=str(rule))
                if resolver is not None:
                    try:
                        resolver(subenv, depends, **matched)
                    except Exception:
                        log.exception('resolve.exception', rule=str(rule))
                        raise
                if action is not None:
                    assert only_action is None
                    only_action = action
                    action_option = matched

        log.debug(
            'resolve.result',
            deps=depends, env=dict(subenv.local_items()),
            action=(only_action and func_name(only_action)),
        )
        result[target] = depends, subenv, only_action, action_option
        pending.extend((dep, subenv.make_child()) for dep in depends if dep not in result)

    return result


def file_newer(f1: str, f2: str):
    return os.stat(f1).st_mtime_ns > os.stat(f2).st_mtime_ns


def file_exist(filename: str):
    return os.path.isfile(filename)


def should_build(target: str, howto: ResolverResults):
    if not file_exist(target):
        return True

    depends, _, _, _ = howto[target]
    for dep in depends:
        _, _, dep_action, _ = howto[dep]
        if not (dep_action and dep_action.is_task) and file_newer(dep, target):
            return True

    return False


def execute(target: str, howto: ResolverResults, visited=None):
    visited = visited or set()
    visited.add(target)

    log = logger.bind(target=target)
    log.info('execute.begin')

    depends, env, action, action_option = howto[target]
    for dep in depends:
        if dep not in visited:
            execute(dep, howto, visited=visited)

    if should_build(target, howto):
        if action is None:
            log.error('execute.no_action')
            raise NoAction(target)

        log.info('execute.action', action=func_name(action))
        try:
            action(env, depends, **action_option)
        except Exception:
            log.exception('execute.exception')
            raise

    if (not (action and action.is_task)) and should_build(target, howto):
        log.error('execute.no_result')
        raise ActionNoResult

    log.info('execute.finish')
