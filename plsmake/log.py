import logging
import time

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


def config_logger(verbose=0):
    if verbose >= 2:
        level = logging.DEBUG
    elif verbose >= 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    processors = [
        add_log_level,
        add_timestamp,
        format_exc_info,
        StackInfoRenderer(),
        LogRenderer(level=level),
    ]
    configure(processors=processors)
