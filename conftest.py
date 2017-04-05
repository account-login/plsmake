"""
pytest source ordering plugin
from https://pagure.io/python-pytest-sourceorder/blob/master/f/pytest_sourceorder.py
"""

import inspect
import pytest


def get_lineno(func):
    unwrapped = inspect.unwrap(func)    # unwrap all decorators
    return unwrapped.__code__.co_firstlineno


def decorate_items(items):
    node_indexes = {}
    for index, item in enumerate(items):
        try:
            func = item.function
        except AttributeError:
            yield (index,), item
            continue

        key = (index,)
        for node in reversed(item.listchain()):
            # Find the corresponding class
            if isinstance(node, pytest.Class):
                cls = node.cls
            else:
                continue

            node_index = node_indexes.setdefault(node, index)
            # Find first occurence of the method in class hierarchy
            for i, parent_class in enumerate(reversed(cls.mro())):
                method = getattr(parent_class, func.__name__, None)
                if method:
                    # Sort methods as tuples (
                    #   position of the class in the inheritance chain,
                    #   position of the method within that class,
                    # )
                    key = (node_index, 0, i, get_lineno(method), index)
                    break
            else:
                # Weird case fallback
                # Method name not in any of the classes in MRO, run it last
                key = (node_index, 1, get_lineno(func), index)
            break

        yield key, item


def pytest_collection_modifyitems(session, config, items):
    items[:] = [item for key, item in sorted(decorate_items(items))]
