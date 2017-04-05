from contextlib import contextmanager

import pytest

import plsmake.app
from plsmake.app import DuplicatedRule, load_string, resolve, execute
from plsmake.env import Env
from plsmake.rule import Rule
from plsmake.utils import func_name


TEST_SOURCE = """
from time import time
from plsmake.api import *

genv = get_env()
genv['a'] = 'a'
genv['CC'] = 'gcc'
genv['CFLAGS'] += ['-O2']

try:
    compiled
except NameError:
    compiled = []

try:
    file_times
except NameError:
    file_times = dict()


@deps('test_{name}')
def unittest(env, depends, name):
    env['CFLAGS'] += ['-DRUN_TEST']
    depends.append('test_{name}.o'.format_map(locals()))
    depends.append('{name}.o'.format_map(locals()))

@action('test_{name}')
def unittest(env, depends, name):
    compiled.append('haha')
    file_times['test_' + name] = time()

@deps('{name}.o')
def compile_object(env, depends, name):
    depends.append('{name}.c'.format_map(locals()))

@action('{name}.o')
def compile_object(env, depends, name):
    compiled.append(name)
    file_times[name + '.o'] = time()
    

@deps('{name}.c')
def haha(env, depends, name):
    env['haha'] = 'haha'

@task('clean')
def clean():
    pass
    """


def test_load_string():
    init_env = Env()
    init_env['CC'] = 'cc'
    init_env['CFLAGS'] = ['-Wall']

    rule_list, env = load_string(TEST_SOURCE, init_env)

    assert list(rule_list.keys()) == [
        Rule('test_{name}'), Rule('{name}.o'), Rule('{name}.c'), Rule('clean')
    ]
    resolver, action = rule_list[Rule('test_{name}')]
    assert func_name(resolver) == func_name(action) == 'unittest'

    resolver, action = rule_list[Rule('{name}.o')]
    assert func_name(resolver) == func_name(action) == 'compile_object'
    assert not action.is_task

    resolver, action = rule_list[Rule('clean')]
    assert action.is_task

    assert init_env['CC'] == 'cc'
    assert init_env['CFLAGS'] == ['-Wall']
    assert env['CC'] == 'gcc'
    assert env['CFLAGS'] == ['-Wall', '-O2']


def test_load_string_dup_rule():
    source = """
from plsmake.api import *

@deps('asdf')
def asdf():
    pass

@deps('asdf')
def asdf():
    pass
    """

    with pytest.raises(DuplicatedRule):
        load_string(source, Env())


def test_resolve():
    init_env = Env()
    init_env['CC'] = 'cc'
    init_env['CFLAGS'] = ['-Wall']

    rule_list, env = load_string(TEST_SOURCE, init_env)
    result = resolve('test_asdf', rule_list, env)

    deps_map = dict(
        (target, deps) for target, (deps, env, action, action_option) in result.items()
    )
    assert deps_map == {
        'test_asdf': ['test_asdf.o', 'asdf.o'],
        'test_asdf.o': ['test_asdf.c'],
        'asdf.o': ['asdf.c'],
        'test_asdf.c': [],
        'asdf.c': [],
    }

    env_dict1 = dict(a='a', CC='gcc', CFLAGS=['-Wall', '-O2', '-DRUN_TEST'])
    env_dict2 = env_dict1.copy()
    env_dict2['haha'] = 'haha'
    for target, (deps, env, action, action_option) in result.items():
        if target.endswith('.c'):
            assert dict(env.items()) == env_dict2
        else:
            assert dict(env.items()) == env_dict1

    for target, (deps, env, action, action_option) in result.items():
        if target.endswith('.o'):
            assert func_name(action) == 'compile_object'
            assert action_option['name'].endswith('asdf')
        elif target == 'test_asdf':
            assert func_name(action) == 'unittest'
            assert action_option == dict(name='asdf')
        else:
            assert action is None


@contextmanager
def patch_multi(obj, pairs):
    olds = []
    for attr, new in pairs:
        olds.append((attr, getattr(obj, attr)))
        setattr(obj, attr, new)

    try:
        yield olds
    finally:
        for attr, old in olds:
            setattr(obj, attr, old)


def test_execute():
    file_times = {
        'test_asdf': 10,
        'test_asdf.o': 100,
        'test_asdf.c': 50,
        'asdf.o': 200,
        'asdf.c': 300,
    }

    def file_exist(filename):
        return filename in file_times

    def file_newer(f1, f2):
        return file_times[f1] > file_times[f2]

    compiled = []
    init_env = Env()
    init_env['CFLAGS'] = []
    ns = dict(compiled=compiled, file_times=file_times)
    rule_list, env = load_string(TEST_SOURCE, init_env, exec_ns=ns)
    result = resolve('test_asdf', rule_list, env)
    with patch_multi(plsmake.app, [('file_exist', file_exist), ('file_newer', file_newer)]):
        execute('test_asdf', result)
    assert compiled == ['asdf', 'haha']
