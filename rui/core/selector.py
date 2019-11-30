from Levenshtein import distance
from core import config
import logging

from pprint import pprint

logger = logging.getLogger(__name__)


def _title_comparator(listEntry, torrentCollection):
    return min(
        distance((listEntry.english or '').lower(), torrentCollection.title.lower()),
        distance((listEntry.romaji or '').lower(), torrentCollection.title.lower())
    )


def selectCollection(listEntry, torrentCollections):
    logger.info('Selecting torrent collection for "%s' % listEntry.title)
    best = None
    for collection in torrentCollections:
        logger.debug('Analizing collection: "%s"' % collection.title)
        collection.score = - (
            0.1 * abs(listEntry.format - collection.format)
            + _title_comparator(listEntry, collection) 
            + abs(listEntry.year - collection.year))
        logger.debug('Collection score: "%f"' % collection.score)

        if not best:
            best = collection
            logger.debug('New best: "%s"' % best)
        elif best.score < collection.score:
            best = collection
            logger.debug('New best: "%s"' % best)
    if best:
        logger.info('Best: %s (score: %f)' % (best, best.score))
        return best


def _selectTorrentFromCollection(collection, filters, episode_filter=0):
    best = None
    for torrent in collection.torrents:
        logger.debug('Analizing torrent: %s' % torrent)
        torrent.score = 0

        if episode_filter and episode_filter != torrent.episode:
            continue

        if any(value.lower() in torrent.properties.lower() for value in filters.get('exclude')):
            logger.debug('Excluded: "%s"' % torrent)
            continue

        for value, modificator in filters.get('prefer').items():
            if value.lower() in torrent.properties.lower():
                logger.debug('Prefered "%s" prensent, +%f' % (value, modificator))
                torrent.score += modificator

        seedScore = 0.001 * torrent.seeders
        logger.debug('Seeeders score +%f' % seedScore)
        torrent.score += seedScore

        logger.debug('Final score: %f' % torrent.score)
        if not best:
            best = torrent
            logger.debug('New best: "%s"' % best)
        elif best.score < torrent.score:
            best = torrent
            logger.debug('New best: "%s"' % best)

    if best:
        logger.info('Best: %s (score: %f)' % (best, best.score))
        return best
    else:
        logger.info('No torrents found for "%s" (episode %d)' % (collection.title, episode_filter))



def selectTorrentFromCollection(listEntry, collection, missingEpisodes):
    rtn = []

    if not listEntry.ongoing and listEntry.episodes == len(missingEpisodes):
        logger.debug('Using finished filters')
        torrent = _selectTorrentFromCollection(collection, config.get('downloads.filters.finished'))
        if torrent:
            rtn.append(torrent)
    else:
        logger.debug('Using ongoing filters')
        logger.debug('Missing episodes: %s' % missingEpisodes)
        filters = config.get('downloads.filters.ongoing')

        for episode in missingEpisodes:
            logger.debug('Getting episode %d ' % episode)
            torrent = _selectTorrentFromCollection(collection, filters, episode)
            if torrent:
                rtn.append(torrent)

    return rtn

