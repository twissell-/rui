import os
import re
import glob
import logging
import requests
import tempfile
from core import config
from core.common import sanitize
from core.common import MediaFormat
from core import persistence


logger = logging.getLogger(__name__)


def getDestinationPath(
    listEntry,
    createIfnotExits=False,
    basePath=config.get("torrentLoader.directory"),
    divideByFormat=config.get("torrentLoader.divideByFormat.enabled"),
):
    """Returns the destination (download) path for a given listEntry"""

    libdir = ""
    if divideByFormat:
        divideByFormat = config.get("torrentLoader.divideByFormat")
        libdir = (
            divideByFormat.get("movies")
            if listEntry.format == MediaFormat.MOVIE
            else divideByFormat.get("others")
        )

    rtn = os.path.join(
        basePath,
        libdir,
        config.get("valueOverride." + str(listEntry.id) + ".directory") or "",
        sanitize(listEntry.title),
    )

    if createIfnotExits and not os.path.isdir(rtn):
        os.umask(0)
        os.makedirs(rtn, mode=0o755)

    return rtn


def getEpisodePath(listEntry, episodeNumber, destinationPath=None):
    """If is downloaded, returns de absolute path for the given episodeNumber of a listEntry. False otherwise."""
    pattern = re.compile(r"(\- *|\_| |S[0-9]*E)0*%s( |v|_)" % episodeNumber)
    # searchString = ("%0" + str(len(str(listEntry.episodes))) + "d") % episodeNumber
    # basename = os.path.basename(getDestinationPath(listEntry))
    # for path in glob.glob(os.path.join(getDestinationPath(listEntry), '*', search_string % episodeNumber)):

    logger.debug(
        'Looking for episode: %s - %d with pattern "%s"'
        % (listEntry.title, episodeNumber, pattern)
    )
    destinationPath = destinationPath or getDestinationPath(listEntry)
    episodeFullPath = None
    for rootDir, dirs, files in os.walk(destinationPath):
        if listEntry.episodes == 1 and len(files) >= 1:
            logger.debug("Single episode anime.")
            episodeFullPath = os.path.join(destinationPath, files[0])

            return episodeFullPath
        else:
            for filename in files:
                logger.debug('Filename: "%s"' % filename)
                if pattern.search(filename):
                    logger.debug('Match: "%s"' % pattern.search(filename).group(0))
                    episodeFullPath = os.path.join(destinationPath, filename)
                    logger.debug(
                        'Episode %s found: "%s"' % (episodeNumber, episodeFullPath)
                    )

                    return episodeFullPath

    logger.debug("Episode %s not found." % episodeNumber)
    return False


def getMissingEpisodes(listEntry, path=None):
    """Returns a list of integers with the missing (not downloaded) episodes of a listEntry"""
    missingEpisodes = []
    anime_data = persistence.get(listEntry.id)

    if not anime_data.get("loaded_episodes"):
        anime_data["loaded_episodes"] = []

    logger.info('Looking for missing episodes: "%s"' % listEntry.title)
    for episode in range(listEntry.firstEpisode, listEntry.lastEpisode + 1):
        if anime_data and episode in anime_data.get("loaded_episodes"):
            continue

        if getEpisodePath(listEntry, episode, path):
            anime_data.get("loaded_episodes").append(episode)
        else:
            missingEpisodes.append(episode)
            if listEntry.ongoing:
                # if the anime is ongoing, just look for the next missing episode.
                break

    persistence.set(listEntry.id, anime_data)
    logger.info("Missing episodes: %s" % missingEpisodes)
    return missingEpisodes


def getEpisodes(listEntry, path=None):
    """Returns a list of paths with the downloaded episodes of a listEntry"""
    episodes = []

    for episode in range(listEntry.firstEpisode, listEntry.lastEpisode + 1):
        if getEpisodePath(listEntry, episode, path):
            episodes.append(episode)

    return episodes


def downloadFile(url, filename=None):
    """Downloads the given url into the tmpdir. returns de full path on success, False otherwise"""
    tmpdir = config.get("torrentLoader.tmpdir")
    filename = (
        os.path.join(tmpdir, filename)
        if filename
        else tempfile.mktemp(prefix="rui-", suffix=".tmp", dir="/tmp/")
    )

    try:
        response = requests.get(url, allow_redirects=True)
        with open(filename, "wb") as file_:
            file_.write(response.content)
    except requests.exceptions.ConnectionError as err:
        logger.error('Error downloading "%s":%s' % (filename, err))
        filename = False

    return filename
