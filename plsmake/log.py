import json
import logging
import sys
import time
import traceback

from structlog import configure, DropEvent
from structlog.stdlib import add_log_level
from structlog.processors import format_exc_info, StackInfoRenderer


# from: structlog/stdlib.py
_NAME_TO_LEVEL = {
    'critical': logging.CRITICAL,
    'exception': logging.ERROR,
    'error': logging.ERROR,
    'warn': logging.WARNING,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'notset': logging.NOTSET,
}

_LEVEL_TO_NAME = dict(
    (v, k) for k, v in _NAME_TO_LEVEL.items()
    if k not in ("warn", "notset")
)


def add_timestamp(logger, name, event_dict):
    event_dict['timestamp'] = time.time()
    return event_dict


class LogDispatcher:
    def __init__(self):
        self.handlers = set()

    def add_handler(self, handler):
        self.handlers.add(handler)

    def remove_handler(self, handler):
        self.handlers.remove(handler)

    def __call__(self, logger, name, event_dict):
        for handler in self.handlers:
            try:
                handler(logger, name, event_dict)
            except Exception:
                print('exception thrown by hander %r' % (handler,), file=sys.stderr)
                traceback.print_exc()

        return event_dict


class LogWriter:
    def __init__(self, filename):
        self.filename = filename
        self._fp = open(self.filename, 'at')

    def __call__(self, logger, name, event_dict):
        string = json.dumps(event_dict, default=_json_fallback)
        self._fp.write(string + '\n')

    def __del__(self):
        self._fp.close()


# from structlog/processors.py
def _json_fallback(obj):
    from structlog.threadlocal import _ThreadLocalDictWrapper
    if isinstance(obj, _ThreadLocalDictWrapper):
        return obj._dict
    else:
        try:
            serializer = obj.__json__
        except AttributeError:
            return repr(obj)
        else:
            return serializer()


class LogRenderer:
    def __init__(self, level=logging.INFO):
        self.level = level

    def __call__(self, logger, name: str, event_dict):
        if _NAME_TO_LEVEL[name] < self.level:       # filter by level
            if event_dict['event'] != 'run_cmd':    # run_cmd is shown anyway
                raise DropEvent

        event = event_dict['event']
        name = name.upper()
        pairs = ' '.join(
            '%s=%s' % (key, value)
            for key, value in event_dict.items()
            if key not in {'event', 'level', 'timestamp'}
        )
        return '{name:9s}{event}: {pairs}'.format_map(locals())


_LOG_DISPATCHER = LogDispatcher()


def config_logger(verbose=0, logfile=None):
    if verbose >= 2:
        level = logging.DEBUG
    elif verbose >= 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    if logfile is not None:
        _LOG_DISPATCHER.add_handler(LogWriter(logfile))

    processors = [
        add_log_level,
        add_timestamp,
        format_exc_info,
        StackInfoRenderer(),
        _LOG_DISPATCHER,
        LogRenderer(level=level),
    ]
    configure(processors=processors)
