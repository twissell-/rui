import logging
from enum import Enum

logger = logging.getLogger(__name__)

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
