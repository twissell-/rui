import os
import re
import glob
import logging
from core import config

logger = logging.getLogger(__name__)


def getDestinationPath(listEntry):
    return os.path.join(config.get('downloads.basePath'), listEntry.title)


def getEpisodePath(listEntry, episodeNumber):
    paddedNumber = ("%0" + str(len(str(listEntry.episodes))) + "d") % episodeNumber
    # basename = os.path.basename(getDestinationPath(listEntry))
    # for path in glob.glob(os.path.join(getDestinationPath(listEntry), '*', search_string % episodeNumber)):
    
    logger.debug('Looking for episode: %s' % paddedNumber)
    destinationPath = getDestinationPath(listEntry)
    for r, d, f in os.walk(destinationPath):
        for filename in f:
            if paddedNumber in filename:
                episodeFullPath = os.path.join(destinationPath, filename)
                logger.debug('Episode %s found: "%s"' % (paddedNumber, episodeFullPath))

                return episodeFullPath

    logger.debug('Episode %s not found.' % paddedNumber)

    return False


def getMissingEpisodes(listEntry):
    missingEpisodes = []
    for episode in range(1, listEntry.episodes + 1):
        if not getEpisodePath(listEntry, episode):
            missingEpisodes.append(episode)

    return missingEpisodes

