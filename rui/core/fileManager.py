import os
import re
import glob
import logging
import requests
import tempfile
from core import config

logger = logging.getLogger(__name__)

def getDestinationPath(listEntry, createIfnotExits=False):
    '''Returns the destination (download) path for a given listEntry'''
    rtn = os.path.join(config.get('downloads.directory'), listEntry.title.replace('?','').replace('.', '').replace(':', '').replace('/', ' '))
    if createIfnotExits and not os.path.isdir(rtn):
        os.umask(0)
        os.mkdir(rtn, mode=0o777)
    return rtn


def getEpisodePath(listEntry, episodeNumber):
    '''If is downloaded, returns de absolute path for the given episodeNumber of a listEntry. False otherwise.'''
    pattern = re.compile(r'\- *0*%d( |v)' % episodeNumber)
    # searchString = ("%0" + str(len(str(listEntry.episodes))) + "d") % episodeNumber
    # basename = os.path.basename(getDestinationPath(listEntry))
    # for path in glob.glob(os.path.join(getDestinationPath(listEntry), '*', search_string % episodeNumber)):

    logger.debug('Looking for episode: %d with pattern "%s"' % (episodeNumber, pattern))
    destinationPath = getDestinationPath(listEntry)
    episodeFullPath = None
    for rootDir, dirs, files in os.walk(destinationPath):
        if listEntry.episodes == 1 and len(files) == 1:
            logger.debug('Single episode anime.')
            episodeFullPath = os.path.join(destinationPath, files[0])
        else:
            for filename in files:
                logger.debug('Filename: "%s"' % filename)
                if pattern.search(filename):
                    logger.debug('Match: "%s"' % pattern.search(filename).group(0))
                    episodeFullPath = os.path.join(destinationPath, filename)
                    logger.debug('Episode %s found: "%s"' % (episodeNumber, episodeFullPath))
                    
                    return episodeFullPath

    logger.debug('Episode %s not found.' % episodeNumber)
    return False


def getMissingEpisodes(listEntry):
    '''Returns a list of integers with the missing (not downloaded) episodes of a listEntry'''
    missingEpisodes = []
    first_episode = config.get('downloads.anilistValueOverride.' + str(listEntry.id) + '.firstEpisode') or 1
    total_episodes = first_episode + (listEntry.episodes or 99)

    for episode in range(first_episode, total_episodes):
        if not getEpisodePath(listEntry, episode):
            missingEpisodes.append(episode)
            if listEntry.ongoing:
                # if the anime is ongoing, just look for the next missing episode.
                break

    return missingEpisodes


def downloadFile(url, filename=None):
    '''Downloads the given url into the tmpdir. returns de full path on success, False otherwise'''
    tmpdir = config.get('downloads.tmpdir')
    filename = os.path.join(tmpdir, filename) if filename else tempfile.mktemp(prefix='rui-', suffix='.tmp', dir='/tmp/')

    try:
        response = requests.get(url, allow_redirects=True)
        with open(filename, 'wb') as file_:
            file_.write(response.content)
    except requests.exceptions.ConnectionError as err:
        logger.error('Error downloading "%s":%s' % (filename, err))
        filename = False

    return filename
