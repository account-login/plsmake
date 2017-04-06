import argparse

from plsmake.app import create_init_env, load_file, resolve, execute
from plsmake.log import config_logger


# TODO: --list-deps
# TODO: --dry-run
# TODO: -j
# TODO: auto dependancy with gcc -MM


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', default='Plsmakefile.py', help='build scripts')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase verbosity')
    parser.add_argument('--logfile', help='write log to file')
    parser.add_argument('targets', nargs='+', help='target to build')

    return parser.parse_args()


def main():
    option = parse_args()
    config_logger(verbose=option.verbose, logfile=option.logfile)

    rule_list, env = load_file(option.file, create_init_env())
    for target in option.targets:
        result = resolve(target, rule_list, env)
        execute(target, result)


if __name__ == '__main__':
    main()
