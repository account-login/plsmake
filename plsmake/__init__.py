from structlog import get_logger

from plsmake.log import add_timestamp, config_logger


config_logger()
logger = get_logger(__name__)
