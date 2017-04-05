import time


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
