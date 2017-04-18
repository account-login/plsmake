import argparse

from plsmake import logger
from plsmake.app import create_init_env, load_file, resolve, execute, ResolverResults
from plsmake.log import config_logger


# TODO: --dry-run
# TODO: -j
# TODO: auto dependancy with gcc -MM


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', default='Plsmakefile.py', help='build scripts')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase verbosity')
    parser.add_argument('--logfile', help='write log to file')
    parser.add_argument('--resolve', action='store_true', help='only do dependency resolution')
    parser.add_argument('targets', nargs='+', help='target to build')

    return parser.parse_args()


def print_deps(target: str, resolution: ResolverResults, indent=0, visited=None, stack=None):
    def iprint(*args):
        print('    ' * indent, *args)

    visited = visited or set()
    stack = stack or []
    depends, _, _, _ = resolution[target]
    visited.add(target)
    stack.append(target)
    iprint(target)

    indent += 1
    for dep in depends:
        if dep in stack:
            iprint(dep, '\t# !!!reference parent!!!')
        elif dep in visited and resolution[dep][0]: # dep is visited and has dependencies
            iprint(dep, '\t# children omitted')
        else:
            print_deps(dep, resolution, indent=indent, visited=visited, stack=stack)

    stack.pop()


def main():
    option = parse_args()
    config_logger(verbose=option.verbose, logfile=option.logfile)
    logger.info('app.start')

    rule_list, env = load_file(option.file, create_init_env())
    for target in option.targets:
        logger.info('app.start_target', target=target)
        result = resolve(target, rule_list, env)
        if option.resolve:
            print_deps(target, result)
        else:
            execute(target, result)
        logger.info('app.finish_target', target=target)

    logger.info('app.finish')


if __name__ == '__main__':
    main()
