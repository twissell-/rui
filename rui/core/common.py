import logging
import time

from enum import Enum

logger = logging.getLogger(__name__)


def format_bytes(size):
    power = 2 ** 10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return round(size, 2), power_labels[n] + 'B'


def timed(func):
    """
    Decorator to log execution time of decorated methods methods
    """

    _logger = logging.getLogger(__name__ + '.Timed')

    def wrapped(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        methodName = type(args[0]).__name__ + '.' + func.__name__
        _logger.info('Executed {method} in {time} seconds.'
        .format(method=methodName, time=(time.time() - start)))
        return(res)

    return wrapped


class MediaFormat(Enum):
    TV = 1
    MOVIE = 2
    SPECIAL = 3
    OVA = 4
    ONA = 5
    OTHER = 9

    def __sub__(self, other):
        return self.value - other.value

    @staticmethod
    def map(value):
        if value == 'TV':
            return MediaFormat.TV
        elif value == 'TV_SHORT':
            return MediaFormat.TV
        elif value == 'MOVIE':
            return MediaFormat.MOVIE
        elif value == 'SPECIAL':
            return MediaFormat.SPECIAL
        elif value == 'OVA':
            return MediaFormat.OVA
        elif value == 'ONA':
            return MediaFormat.ONA
        elif value == 'TV Series':
            return MediaFormat.TV
        elif value == 'Movie':
            return MediaFormat.MOVIE
        elif value == 'TV Special':
            return MediaFormat.SPECIAL
        elif value == 'DVD Special':
            return MediaFormat.SPECIAL
        elif value == 'BD Special':
            return MediaFormat.SPECIAL
        else:
            return MediaFormat.OTHER


def sanitize(string):
    return string.replace('?','').replace('.', '').replace(':', '').replace('/', ' ').replace('"','')
