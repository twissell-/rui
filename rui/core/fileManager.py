import os
import re
import glob
import logging
import requests
import tempfile
from core import config
from core.common import sanitize

logger = logging.getLogger(__name__)

def getDestinationPath(listEntry, createIfnotExits=False, basePath=config.get('downloads.directory')):
    '''Returns the destination (download) path for a given listEntry'''
    rtn = os.path.join(basePath, config.get('valueOverride.' + str(listEntry.id) + '.directory') or '', sanitize(listEntry.title))
    if createIfnotExits and not os.path.isdir(rtn):
        os.umask(0)
        os.mkdir(rtn, mode=0o777)

    return rtn


def getEpisodePath(listEntry, episodeNumber, destinationPath=None):
    '''If is downloaded, returns de absolute path for the given episodeNumber of a listEntry. False otherwise.'''
    pattern = re.compile(r'(\- *|\_| )0*%d( |v|_)' % episodeNumber)
    # searchString = ("%0" + str(len(str(listEntry.episodes))) + "d") % episodeNumber
    # basename = os.path.basename(getDestinationPath(listEntry))
    # for path in glob.glob(os.path.join(getDestinationPath(listEntry), '*', search_string % episodeNumber)):

    logger.info('Looking for episode: %s - %d with pattern "%s"' % (listEntry.title, episodeNumber, pattern))
    destinationPath = destinationPath or getDestinationPath(listEntry)
    episodeFullPath = None
    for rootDir, dirs, files in os.walk(destinationPath):
        if listEntry.episodes == 1 and len(files) >= 1:
            logger.info('Single episode anime.')
            episodeFullPath = os.path.join(destinationPath, files[0])
            
            return episodeFullPath
        else:
            for filename in files:
                logger.debug('Filename: "%s"' % filename)
                if pattern.search(filename):
                    logger.debug('Match: "%s"' % pattern.search(filename).group(0))
                    episodeFullPath = os.path.join(destinationPath, filename)
                    logger.info('Episode %s found: "%s"' % (episodeNumber, episodeFullPath))
                    
                    return episodeFullPath

    logger.info('Episode %s not found.' % episodeNumber)
    return False


def getMissingEpisodes(listEntry, path=None):
    '''Returns a list of integers with the missing (not downloaded) episodes of a listEntry'''
    missingEpisodes = []
    first_episode = config.get('valueOverride.' + str(listEntry.id) + '.firstEpisode') or 1
    total_episodes = first_episode + (listEntry.episodes or 99)

    for episode in range(first_episode, total_episodes):
        if not getEpisodePath(listEntry, episode, path):
            missingEpisodes.append(episode)
            if listEntry.ongoing:
                # if the anime is ongoing, just look for the next missing episode.
                break

    return missingEpisodes


def getEpisodes(listEntry, path=None):
    '''Returns a list of paths with the downloaded episodes of a listEntry'''
    episodes = []
    first_episode = config.get('valueOverride.' + str(listEntry.id) + '.firstEpisode') or 1
    total_episodes = first_episode + (listEntry.episodes or 99)

    for episode in range(first_episode, total_episodes):
        if getEpisodePath(listEntry, episode, path):
            episodes.append(episode)

    return episodes


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
