from structlog import get_logger, configure
from structlog.stdlib import add_log_level
from structlog.processors import format_exc_info, StackInfoRenderer

from plsmake.log import add_timestamp, print_log


processors = [
    add_log_level,
    add_timestamp,
    format_exc_info,
    StackInfoRenderer(),
    print_log,
]
configure(processors=processors)

logger = get_logger(__name__)
