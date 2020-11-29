# coding=utf-8
"""
@Author: Liang Chao
@Email: nobody_team@outlook.com
@File: log.py
@Created: 2020/10/23 19:59
@Desc:
"""
import logging
import os
from logging.handlers import RotatingFileHandler

import logzero
from logzero.colors import Fore

LOG_DIR = os.path.expanduser('~')
MAX_LOG_SIZE = 10 * 1024 * 1024  # 限定log 文件最大为10M
BACKUP_COUNT = 20


class MyLogFormatter(logzero.LogFormatter):
    """

    """
    DEFAULT_FORMAT = '%(color)s[%(asctime)s %(module)s:%(lineno)d] [%(levelname)1s]%(end_color)s %(message)s'

    def __init__(self, color=True, datefmt=logging.Formatter.default_time_format, fmt=DEFAULT_FORMAT):
        super().__init__(color=color,
                         datefmt=datefmt,
                         fmt=fmt,
                         colors={
                             logging.DEBUG: Fore.CYAN,
                             logging.INFO: Fore.GREEN,
                             logging.WARNING: Fore.YELLOW,
                             logging.ERROR: Fore.RED,
                         })


def setup_logger(name=None,
                 level=logging.DEBUG,
                 file_level=logging.DEBUG,
                 fmt=MyLogFormatter.DEFAULT_FORMAT,
                 datefmt=logging.Formatter.default_time_format,
                 max_bytes=MAX_LOG_SIZE,
                 backup_count=BACKUP_COUNT,
                 disable_stderr=False):
    fmt = fmt or logzero.LogFormatter.DEFAULT_FORMAT
    _name = name if name.endswith('.log') else f'{name}.log'
    _name = os.path.join(LOG_DIR, 'logs', _name)
    log_dir = os.path.dirname(_name)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    _logger = logging.getLogger(_name or __name__)
    _logger.propagate = False
    _logger.setLevel(level)

    # Reconfigure existing handlers
    stderr_stream_handler = None
    for handler in list(_logger.handlers):
        if hasattr(handler, logzero.LOGZERO_INTERNAL_LOGGER_ATTR):
            if isinstance(handler, logging.FileHandler):
                _logger.removeHandler(handler)
                continue
            elif isinstance(handler, logging.StreamHandler):
                stderr_stream_handler = handler
        handler.setLevel(level)
        handler.setFormatter(MyLogFormatter(datefmt=datefmt, fmt=fmt))

    # remove the stderr handler (stream_handler) if disabled
    if disable_stderr:
        if stderr_stream_handler is not None:
            _logger.removeHandler(stderr_stream_handler)
    elif stderr_stream_handler is None:
        stderr_stream_handler = logging.StreamHandler()
        setattr(stderr_stream_handler, logzero.LOGZERO_INTERNAL_LOGGER_ATTR, True)
        stderr_stream_handler.setLevel(level)
        stderr_stream_handler.setFormatter(MyLogFormatter(datefmt=datefmt, fmt=fmt))
        _logger.addHandler(stderr_stream_handler)

    if file_level:
        filename = _name
        filename = os.path.join(LOG_DIR, 'logs', filename)
        rotating_file_handler = RotatingFileHandler(filename=filename, maxBytes=max_bytes, backupCount=backup_count,
                                                    encoding="utf-8")
        setattr(rotating_file_handler, logzero.LOGZERO_INTERNAL_LOGGER_ATTR, True)
        rotating_file_handler.setLevel(file_level)
        rotating_file_handler.setFormatter(MyLogFormatter(color=False, datefmt=datefmt, fmt=fmt))
        _logger.addHandler(rotating_file_handler)
    return _logger


def close_logger(log):
    if not log:
        return
    for handler in log.handlers:
        if hasattr(handler, 'close'):
            handler.close()


class LogParser:
    def __init__(self, file, cache_size=1000, ):
        self.file = file
        self._cache_size = cache_size
        self._line_cache = []  # 行缓存
        self._suffix_lines = 1000

    def filter(self, keywords, encoding='utf-8'):
        lines = []
        caught = 0
        with open(self.file, 'r', encoding=encoding) as f:
            line = f.readline()
            line = str(line, encoding='utf-8')
            self._line_cache.append(line)
            if len(self._line_cache) > self._cache_size:
                self._line_cache.pop(0)  # 只保留一定行数，超出则丢弃列表头部元素
            if keywords in line:
                caught += 1
                if not lines:
                    lines.extend(self._line_cache)


logger = setup_logger('nobody', level=logging.DEBUG, file_level=logging.DEBUG)
