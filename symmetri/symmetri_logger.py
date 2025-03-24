import json
import logging
import sys

import urllib3
from loguru import logger

# Disable specific warning to prevent log contamination
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Format output for loguru.logger
def serialize(record):
    subset = {
        "ts": record["time"].isoformat(sep=' ', timespec='milliseconds'),
        "level": record["level"].name,
        "location": '%s => %s => %s' % (record["file"].name, record["function"], record["line"]),
        "message": record["message"],
    }
    return json.dumps(subset, default=str)


def patching(record):
    record["extra"]["serialized"] = serialize(record)


# Setup logging format
logger = logger.patch(patching)


# Class to intercept standard logging into loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# Setup logs with intercepting standard logging
def setup_logs(log_level_str: str) -> None:
    # setup loguru.logger
    logger.remove(0)
    logger.add(
        sys.stderr,
        level=log_level_str,
        format="{extra[serialized]}",
        backtrace=False,
        diagnose=False,
    )
    logger.debug("Initialized logger in loguru.")

    # intercept standard logging
    log_level = getattr(logging, log_level_str, logging.NOTSET)
    logging.basicConfig(handlers=[InterceptHandler()], level=log_level, force=True)

    # setup standard logging
    logger.debug(f'Log level set as {log_level_str}')

    # Disable detailed logs from requests
    logging.getLogger("requests").setLevel(max(log_level, logging.WARNING))
    logging.getLogger("urllib3").setLevel(max(log_level, logging.WARNING))
    logging.getLogger("web3http").setLevel(max(log_level, logging.WARNING))

    # disable detailed logs from boto
    logging.getLogger('boto3').setLevel(max(log_level, logging.WARNING))
    logging.getLogger('botocore').setLevel(max(log_level, logging.WARNING))

    # disable details from postgres
    logging.getLogger('psycopg').setLevel(max(log_level, logging.WARNING))
    logging.getLogger('snowflake').setLevel(max(log_level, logging.WARNING))
    logging.getLogger('snowflake.connector').setLevel(max(log_level, logging.WARNING))

    logging.getLogger('openai').setLevel(max(log_level, logging.WARNING))
    logging.getLogger('anthropic').setLevel(max(log_level, logging.WARNING))
