from plsmake.rule import Rule


def test_rule_match():
    def R(url, target, expect):
        assert Rule(url).match(target) == expect

    R('asdf', 'asdf', dict())
    R('asdf', 'asdff', None)
    R('asdf', 'asd', None)
    R('asdf{a}b{c}', 'asdf1b3', dict(a='1', c='3'))
    R('asdf{a}{c}', 'asdf1b3', dict(a='1b', c='3'))
    R('asdf{a}', 'asdf', None)


def test_rule_eq_hash():
    assert Rule('asdf') == Rule('asdf')
    assert hash(Rule('bbb')) == hash(Rule('bbb'))
