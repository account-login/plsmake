import unittest

from plsmake.helpers import parse_make_deps, MakeDepsParser


class TestParseMakeDeps(unittest.TestCase):
    method = staticmethod(parse_make_deps)

    def test_run(self):
        s = r"""asdf: as \
            asdf  12\ 34 \
            qwer
        """
        assert self.method(s) == dict(asdf=['as', 'asdf', '12 34', 'qwer'])

        s = r"""
        as\ df  :  as \

        qwer:
        zxcv:123
        """
        assert self.method(s) == {'as df': ['as'], 'qwer': [], 'zxcv': ['123']}


class TestParseMakeDepsAlt(TestParseMakeDeps):
    def setUp(self):
        self.parser = MakeDepsParser()

    def method(self, s):
        return self.parser.parse(s)
