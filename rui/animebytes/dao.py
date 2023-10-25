import json
import logging
from time import sleep

import requests

from rui.animebytes.model import TorrentCollection
from rui.common import config
from rui.common.utils import sanitize

logger = logging.getLogger(__name__)

_ENDPOINT = "https://animebytes.tv/scrape.php?torrent_pass={torrentPass}&format=anime&username={username}&searchstr={searchstr}&filter_cat%5B1%5D&type=anime"


def getTorrentCollectionByAnime(anime):
    rtn = []
    if anime.title and not rtn:
        rtn = getTorrentCollectionByTitle(anime.title)
    if anime.romaji and not rtn:
        sleep(1)
        logger.info("Retrying with romaji title.")
        rtn = getTorrentCollectionByTitle(anime.romaji)
    if anime.native and not rtn:
        sleep(1)
        logger.info("Retrying with native title.")
        rtn = getTorrentCollectionByTitle(anime.native)
    if anime.english and not rtn:
        sleep(1)
        logger.info("Retrying with english title.")
        rtn = getTorrentCollectionByTitle(anime.english)
    if anime.romaji and not rtn:
        sleep(1)
        logger.info("Retrying with sanitize romaji title.")
        rtn = getTorrentCollectionByTitle(sanitize(anime.romaji))
    if anime.english and not rtn:
        sleep(1)
        logger.info("Retrying with sanitize english title.")
        rtn = getTorrentCollectionByTitle(sanitize(anime.english))

    return rtn


def getTorrentCollectionByTitle(title):
    logger.info('Getting torrents list for "%s"' % title)

    try:
        response = requests.get(
            _ENDPOINT.format(
                torrentPass=config.get("animebytes.torrentPass"),
                username=config.get("animebytes.username"),
                searchstr=title,
            )
        ).json()
        logger.debug("Raw response: " + json.dumps(response, indent=2))
    except json.JSONDecodeError as e:
        logger.error("Error parsing json for %s." % title)
        logger.error(e)
        return []

    if response.get("Matches") == 0:
        logger.info("No results found.")
        return []

    rtn = []
    for anime in response.get("Groups"):
        rtn.append(TorrentCollection(anime))

    logger.debug("Mapped respose: " + str(rtn))
    return rtn
