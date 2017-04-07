from plsmake.api import run_with_output


def extend_depends_by_compiler(env, depends):
    output = run_with_output(env['CXX'], *env['CXXFLAGS'], '-MM', '-MT', 'dummy', *depends)
    extra_deps = parse_make_deps(output.decode())['dummy']
    for dep in extra_deps:
        if dep not in depends:
            depends.append(dep)


_WORD_BREAK = object()
_LINE_BREAK = object()


def _split_gen(string: str):
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
