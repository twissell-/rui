#!/usr/bin/env python3

import logging
from logging.handlers import RotatingFileHandler

from core import (
    anilist,
    animebytes,
    selector,
    fileManager,
    config
)
from pprint import pprint

root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)

loghandler = logging.handlers.RotatingFileHandler(
    '/etc/rui/error.log', maxBytes=100 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s - %(name)s ln.%(lineno)d - %(message)s')

loghandler.setFormatter(formatter)
root_logger.addHandler(loghandler)

logger = logging.getLogger('cli')

for anime in anilist.getWatchingListByUsername(config.get('anilist.username')):
    if anime.notes and 'rui.ignore' in anime.notes:
        continue
    print('=' * 120)
    print('Anime:', anime)
    
    missingEpisodes = fileManager.getMissingEpisodes(anime)
    if not missingEpisodes:
        print('All episodes of %s have been downloaded.' % anime.title)
        continue
    print('Missing Episodes: ', missingEpisodes)
    
    collection = selector.selectCollection(anime, animebytes.getTorrentCollectionByTitle(anime.title))
    if not collection:
        print('No torrents found for "%s"' % anime.title)
        continue
    print('Collection:', collection)
    torrents = selector.selectTorrentFromCollection(anime, collection, missingEpisodes)
    pprint(torrents)
