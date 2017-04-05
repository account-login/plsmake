import re


class Rule:
    OPEN_MARK = r'\{'
    CLOSE_MAKR = r'\}'
    ID_RE = r'[a-zA-Z_]\w*'
    VALUE_RE = r'([\w-]+)'

    def __init__(self, url: str):
        self.url = url
        self.words, self.params = self.parse(url)
        regex = self.VALUE_RE.join(re.escape(wd) for wd in self.words)
        regex = '^{}$'.format(regex)
        self.match_re = re.compile(regex)

    @classmethod
    def parse(cls, url: str):
        regex = re.compile(cls.OPEN_MARK + cls.ID_RE + cls.CLOSE_MAKR)
        words = regex.split(url)
        params = regex.findall(url)
        assert len(params) + 1 == len(words)
        return words, [ par[1:-1] for par in params ]   # {xxx} -> xxx

    def match(self, target: str):
        matched = self.match_re.fullmatch(target)
        if matched:
            return dict(zip(self.params, matched.groups()))
        else:
            return None

    def __str__(self):
        return self.url

    def __repr__(self):
        return '<Rule %s>' % (self.url,)

    def __eq__(self, other):
        return self.url == other.url

    def __hash__(self):
        return hash(self.url)
