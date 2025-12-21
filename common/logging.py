import logging
import sys
from pythonjsonlogger import jsonlogger


def setup_logging(level: str) -> None:
    logger = logging.getLogger()
    logger.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(trace_id)s",
        rename_fields={"levelname": "level", "asctime": "ts"},
    )
    handler.setFormatter(formatter)

    logger.handlers = [handler]
