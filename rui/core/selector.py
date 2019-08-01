from Levenshtein import distance
import logging
from pprint import pprint

logger = logging.getLogger(__name__)

def selectCollection(listEntry, torrentCollection):
    logger.info('Selecting torrent collection for "%s' % listEntry.title)
    best = None
    for result in torrentCollection:
        logger.debug('Analizing "%s"' % result.title)
        result.score = - (
            0.1 * abs(listEntry.format - result.format)
            + title_comparator(listEntry, result) 
            + abs(listEntry.year - result.year))

        if not best:
            best = result
        elif best.score < result.score:
            best = result

    if best:
        return best

def title_comparator(listEntry, torrentCollection):
    return min(
        distance((listEntry.english or '').lower(), torrentCollection.title.lower()),
        distance((listEntry.romaji or '').lower(), torrentCollection.title.lower())
    )
