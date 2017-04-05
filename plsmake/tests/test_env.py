import unittest

import pytest

from plsmake.env import Env


class TestEnv(unittest.TestCase):
    def setUp(self):
        self.parent = Env()
        self.parent['a'] = 'a'
        self.parent['b'] = 'b'
        self.parent['list'] = [1, 2]
        self.parent['list2'] = [1, 2, 3]

        self.child = self.parent.make_child()

    def test_access(self):
        assert self.parent['a'] == 'a'
        assert self.parent.get('a') == 'a'
        lst = [1, 2]
        self.parent['list1'] = lst
        assert self.parent['list1'] is lst

        assert self.parent.get('xxx', 1) == 1
        with pytest.raises(KeyError) as exc_info:
            self.parent['xxx']
            assert exc_info.value.args == ('xxx',)

    def test_remove(self):
        self.parent['c'] = 'c'
        del self.parent['c']
        with pytest.raises(KeyError) as exc_info:
            self.parent['c']
            assert exc_info.value.args == ('c',)
        # re-set
        self.parent['c'] = 'cc'
        assert self.parent['c'] == 'cc'

    def test_inherits(self):
        assert self.child['a'] == 'a'

    def test_child_remove(self):
        del self.child['a']
        with pytest.raises(KeyError) as exc_info:
            self.child['a']
            assert exc_info.value.args == ('a',)
        assert self.parent['a'] == 'a'

    def test_child_modify(self):
        self.child['b'] = 'bb'
        assert self.child['b'] == 'bb'
        assert self.parent['b'] == 'b'

    def test_child_mutable(self):
        clst = self.child['list']
        clst.append(3)
        assert self.child['list'] == [1, 2, 3]
        assert self.parent['list'] == [1, 2]

        self.child['list2'] += [4, 5]
        assert self.child['list2'] == [1, 2, 3, 4, 5]
        assert self.parent['list2'] == [1, 2, 3]

    def test_items(self):
        self.child['c'] = 'c'
        self.child['b'] = 'bb'
        del self.child['a']

        common = [('list', [1, 2]), ('list2', [1, 2, 3])]
        parent_dict = dict([('a', 'a'), ('b', 'b')] + common)
        assert dict(self.child.items()) == dict([('b', 'bb'), ('c', 'c')] + common)
        assert dict(self.parent.items()) == parent_dict

        assert dict(self.child.local_items()) == dict(b='bb', c='c', a=None)
        assert dict(self.parent.local_items()) == parent_dict
