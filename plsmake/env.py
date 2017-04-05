from collections import abc


class Env:
    def __init__(self, init_dict=None):
        self._local = dict()
        if init_dict is not None:
            self._local.update(init_dict)
        self._removed = set()
        self.parent = None

    def __setitem__(self, key, value):
        self._local[key] = value
        self._removed.discard(key)

    def __getitem__(self, key):
        if key in self._removed:
            raise KeyError(key)

        try:
            return self._local[key]
        except KeyError:
            if self.parent is not None:
                ret = self.parent[key]
                # XXX: copy mutable data from parent
                if isinstance(ret, (abc.MutableSequence, abc.MutableMapping, abc.MutableSet)):
                    ret = ret.copy()
                    self._local[key] = ret
                return ret
            else:
                raise

    def __delitem__(self, key):
        self._removed.add(key)
        self._local.pop(key, None)

    def update(self, other):
        for key, value in other.items():
            self[key] = value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def items(self):
        """Return items from local and parent."""
        yield from self._local.items()
        if self.parent is not None:
            for key, value in self.parent.items():
                if key not in self._removed and key not in self._local:
                    yield key, value

    def local_items(self):
        """Return local items. Removed values are represented with None."""
        for key, value in self._local.items():
            if self.parent is not None:
                if self.parent.get(key) == value:
                    continue
            yield key, value

        for key in self._removed:
            yield key, None

    def make_child(self) -> 'Env':
        """Return a child environment that inherits from self."""
        ret = type(self)()
        ret.parent = self
        return ret
