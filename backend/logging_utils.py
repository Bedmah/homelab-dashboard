import logging
import os
from collections import deque
from logging.handlers import RotatingFileHandler

from .config import ACCESS_LOG_FILE, APP_LOG_FILE, LOG_DIR

APP_LOGGER = logging.getLogger("bedmah.app")
ACCESS_LOGGER = logging.getLogger("bedmah.access")


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)

    if not APP_LOGGER.handlers:
        APP_LOGGER.setLevel(logging.INFO)
        app_handler = RotatingFileHandler(APP_LOG_FILE, maxBytes=2_000_000, backupCount=8, encoding="utf-8")
        app_handler.setFormatter(logging.Formatter("%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"))
        APP_LOGGER.addHandler(app_handler)
        APP_LOGGER.propagate = False

    if not ACCESS_LOGGER.handlers:
        ACCESS_LOGGER.setLevel(logging.INFO)
        access_handler = RotatingFileHandler(ACCESS_LOG_FILE, maxBytes=2_000_000, backupCount=8, encoding="utf-8")
        access_handler.setFormatter(logging.Formatter("%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"))
        ACCESS_LOGGER.addHandler(access_handler)
        ACCESS_LOGGER.propagate = False


def kv_dump(**kwargs):
    items = []
    for key, value in kwargs.items():
        if value is None:
            continue
        text = str(value).replace("\n", "\\n")
        items.append(f"{key}={text}")
    return " ".join(items)


def app_log(level, event, **kwargs):
    msg = event
    tail = kv_dump(**kwargs)
    if tail:
        msg += f" | {tail}"
    APP_LOGGER.log(level, msg)


def read_log_tail(path, max_lines=300):
    max_lines = max(1, min(2000, int(max_lines)))
    if not os.path.isfile(path):
        return []
    dq = deque(maxlen=max_lines)
    with open(path, "r", encoding="utf-8", errors="replace") as file_obj:
        for line in file_obj:
            dq.append(line.rstrip("\r\n"))
    return list(dq)
