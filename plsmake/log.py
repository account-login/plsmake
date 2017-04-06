import time

from structlog import configure
from structlog.stdlib import add_log_level
from structlog.processors import format_exc_info, StackInfoRenderer


def add_timestamp(logger, name, event_dict):
    event_dict['timestamp'] = time.time()
    return event_dict


def print_log(logger, name: str, event_dict):
    event = event_dict['event']
    name = name.upper()
    pairs = ' '.join(
        '%s=%s' % (key, value)
        for key, value in event_dict.items()
        if key not in {'event', 'level', 'timestamp'}
    )
    return '{name:9s}{event}: {pairs}'.format_map(locals())


def config_logger():
    processors = [
        add_log_level,
        add_timestamp,
        format_exc_info,
        StackInfoRenderer(),
        print_log,
    ]
    configure(processors=processors)
