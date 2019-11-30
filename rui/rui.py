#!/usr/bin/env python3

import logging
import argparse
from logging.handlers import RotatingFileHandler

from core import (
    anilist,
    animebytes,
    selector,
    fileManager,
    config
)
from core.torrentClient import TorrentClient
from pprint import pprint

root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)

loghandler = logging.handlers.RotatingFileHandler(
    './rui.log', maxBytes=10 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s - %(name)s ln.%(lineno)d - %(message)s')


loghandler.setFormatter(formatter)
root_logger.addHandler(loghandler)

logger = logging.getLogger('cli')

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true', help='Does add the torrent to transmission .')
parser.add_argument('-v', '--verbose', action='store_true', help='Explain what it\'s being done')

def process(isDryRun=False, verbose=False):
    for anime in anilist.getWatchingListByUsername(config.get('anilist.username')):
        if anime.notes and 'rui.ignore' in anime.notes:
            continue
        if verbose: 
            print('=' * 120)
            print('Anime:', anime)
            print('Destination: ', fileManager.getDestinationPath(anime, True))

        missingEpisodes = fileManager.getMissingEpisodes(anime)
        if not missingEpisodes:
            if verbose: print('All episodes of %s have been downloaded.' % anime.title)
            continue
        if verbose: print('Missing Episodes: ', missingEpisodes)

        collection = selector.selectCollection(anime, animebytes.getTorrentCollectionByTitle(anime.title))
        if not collection:
            if verbose: print('No torrent collection found for "%s"' % anime.title)
            continue
        if verbose: print('Collection:', collection)

        torrents = selector.selectTorrentFromCollection(anime, collection, missingEpisodes)
        if not torrents:
            if verbose: print('No torrents found for "%s" %s' % (anime.title, str(missingEpisodes)))
            continue

        tc = TorrentClient()
        for torrent in torrents:
            if verbose: print('Torrent: ', torrent)
            if not isDryRun:
                tc.add(torrent.url, fileManager.getDestinationPath(anime, True))


if __name__ == "__main__":
    args = parser.parse_args()
    process(isDryRun=args.dry_run, verbose=args.verbose)