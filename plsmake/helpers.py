import os
from typing import Optional, Sequence

from plsmake import logger
from plsmake.api import run_with_output


SOURCE_SUFFIX = [
    '.c', '.cc', '.cpp', '.cxx', '.c++',
    '.h', '.hh', '.hpp', '.hxx',
]
CACHE_DIR = '.plscache'


def is_source(filename: str):
    filename = filename.lower()
    for suff in SOURCE_SUFFIX:
        if filename.endswith(suff):
            return True
    return False


def file_time(filename: str):
    return os.stat(filename).st_mtime_ns


def normpath(path: str):
    return os.path.normpath(path).replace('\\', '/')


def joinpath(path1, path2):
    return normpath(os.path.join(path1, path2))


def get_deps_with_cxx(env, sourcefile: str) -> Sequence[str]:
    cmd = [env['CXX'], '-MM', '-MT', 'dummy'] + env['CXXFLAGS'] + [sourcefile]
    output = run_with_output(*cmd)
    depends = parse_make_deps(output.decode())['dummy']
    return [normpath(dep) for dep in depends]


def get_deps_cache_filename(sourcefile: str):
    return joinpath(CACHE_DIR, sourcefile) + '.deps'


def get_deps_with_cache(env, sourcefile: str) -> Optional[Sequence[str]]:
    cache_file = get_deps_cache_filename(sourcefile)
    cache_dir = os.path.dirname(cache_file)
    if not os.path.isdir(cache_dir):
        logger.debug('get_deps.make_dir', dir=cache_dir)
        try:
            os.makedirs(cache_dir, exist_ok=True)
        except OSError:
            logger.exception('get_deps.make_dir_fail')
            return None

    if not os.path.exists(cache_file):
        logger.debug('get_deps.no_cache')
        return None

    with open(cache_file, 'rt', encoding='utf8') as fp:
        depends = fp.read().splitlines()

    cache_time = file_time(cache_file)
    for dep in [sourcefile] + depends:
        if not os.path.exists(dep) or file_time(dep) > cache_time:
            logger.debug('get_deps.cache_expire', cache_file=cache_file, dep=dep)
            return None

    return depends


def set_deps_cache(env, sourcefile: str, depends: Sequence[str]):
    cache_file = get_deps_cache_filename(sourcefile)
    logger.debug('get_deps.set_cache', cache_file=cache_file)
    with open(cache_file, 'wt+', newline='\n', encoding='utf8') as fp:
        fp.write('\n'.join(depends) + '\n')


def get_deps(env, sourcefile: str) -> Sequence[str]:
    depends = get_deps_with_cache(env, sourcefile)
    if depends is None:
        depends = get_deps_with_cxx(env, sourcefile)
        set_deps_cache(env, sourcefile, depends)
        cache_hit = False
    else:
        cache_hit = True

    logger.debug('get_deps.result', depends=depends, cache_hit=cache_hit)
    return depends


def extend_depends_by_compiler(env, depends):
    srcs = [dep for dep in depends if is_source(dep)]
    for sourcefile in srcs:
        extra_deps = get_deps(env, sourcefile)
        for dep in extra_deps:
            if dep not in depends:
                depends.append(dep)


_WORD_BREAK = object()
_LINE_BREAK = object()


def _split_gen(string: str):
    string = string.replace('\r\n', '\n')
    escaping = False
    for ch in string:
        if escaping:
            escaping = False
            if ch != '\n':
                yield ch
        else:
            if ch == '\\':
                escaping = True
            elif ch == '\n':
                yield _LINE_BREAK
            elif ch.isspace():
                yield _WORD_BREAK
            else:
                yield ch

    assert not escaping


def _split(string):
    def push_word():
        nonlocal word
        if word:
            line.append(word)
            word = ''

    word = ''
    line = []
    for ch in _split_gen(string):
        if ch is _LINE_BREAK:
            push_word()
            if line:
                yield line
                line = []
        elif ch is _WORD_BREAK:
            push_word()
        else:
            word += ch

    push_word()
    if line:
        yield line


def parse_make_deps(string: str):
    ans = dict()
    for line in _split(string):
        target, *remain = line
        if ':' in target:
            target, _, r1 = target.partition(':')
            if r1:
                remain.insert(0, r1)
        else:
            assert remain[0].startswith(':')
            remain[0] = remain[0][1:]
            if not remain[0]:
                remain.pop(0)

        assert target == target.strip()
        target = target.strip()
        ans.setdefault(target, [])
        ans[target].extend(remain)
    return ans


class ParseMakeDepsError(Exception):
    pass


def _expect(ch, cond, msg=None):
    if not cond:
        raise ParseMakeDepsError(ch, msg)


# noinspection PyAttributeOutsideInit
class MakeDepsParser:
    def __init__(self):
        self._init()

    def _init(self):
        self.ans = dict()
        self.target = ''
        self.word = ''
        self.deps = []

        self.state = self.st_start

    def parse(self, string):
        for ch in string:
            self.state(ch)
        self.finish()

        ans = self.ans
        self._init()
        return ans

    def st_start(self, ch):
        if not ch.isspace():
            self.target = ch
            self.state = self.st_target_mid

    def st_target_mid(self, ch):
        _expect(ch, ch != '\n')
        if ch == '\\':
            self.state = self.st_target_esc
        elif ch.isspace():
            self.state = self.st_colon
        elif ch == ':':
            self.state = self.st_word_start
        else:
            self.target += ch

    def st_target_esc(self, ch):
        if ch != '\n':
            self.target += ch
        self.state = self.st_target_mid

    def st_colon(self, ch):
        if ch == ':':
            self.state = self.st_word_start
        else:
            _expect(ch, ch.isspace() and ch != '\n')

    def _collect_deps(self):
        if self.word:
            self.deps.append(self.word)
        if self.target:
            self.ans[self.target] = self.deps
        self.target = ''
        self.word = ''
        self.deps = []

    def st_word_start(self, ch):
        if ch == '\n':
            self._collect_deps()
            self.state = self.st_start
        elif ch.isspace():
            pass
        elif ch == '\\':
            self.state = self.st_word_newline
        else:
            self.word = ch
            self.state = self.st_word_mid

    def st_word_newline(self, ch):
        _expect(ch, ch == '\n')
        self.state = self.st_word_start

    def st_word_mid(self, ch):
        if ch == '\\':
            self.state = self.st_word_esc
        elif ch == '\n':
            self._collect_deps()
            self.state = self.st_start
        elif ch.isspace():
            assert self.word
            self.deps.append(self.word)
            self.word = ''
            self.state = self.st_word_start
        else:
            self.word += ch

    def st_word_esc(self, ch):
        if ch != '\n':
            self.word += ch
        self.state = self.st_word_mid

    def finish(self):
        if self.state not in {self.st_start, self.st_word_start, self.st_word_mid}:
            raise ParseMakeDepsError
        self._collect_deps()
