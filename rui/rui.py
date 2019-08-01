import logging
from logging.handlers import RotatingFileHandler

from core import (
    anilist,
    animebytes,
    selector,
    config
)
from pprint import pprint

root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)

loghandler = logging.handlers.RotatingFileHandler(
    './error.log', maxBytes=100 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s - %(name)s ln.%(lineno)d - %(message)s')

loghandler.setFormatter(formatter)
root_logger.addHandler(loghandler)

logger = logging.getLogger('cli')

for anime in anilist.getWatchingListByUsername(config.get('anilist.username')):
    selector.selectCollection(anime, animebytes.getTorrentCollectionByTitle(anime.title))
