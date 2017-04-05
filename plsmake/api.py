import subprocess

from plsmake import logger
from plsmake.app import get_context


def get_env():
    return get_context().get_env()


def deps(urle_url):
    return get_context().deps(urle_url)


def action(rule_url):
    return get_context().action(rule_url)


def task(rule_url):
    return get_context().task(rule_url)


def run(*args):
    logger.info('run_cmd', args=args)
    subprocess.check_call(args)
