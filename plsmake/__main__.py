import argparse

from plsmake.app import create_init_env, load_file, resolve, execute


# TODO: --verbose
# TODO: --list-deps
# TODO: --dry-run


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', default='Plsmakefile.py')
    parser.add_argument('targets', nargs='+')

    return parser.parse_args()


def main():
    option = parse_args()
    rule_list, env = load_file(option.file, create_init_env())
    for target in option.targets:
        result = resolve(target, rule_list, env)
        execute(target, result)


if __name__ == '__main__':
    main()
