import json
import logging
from datetime import datetime, timedelta
from time import sleep
from typing import List

import requests

from rui.anilist import query
from rui.anilist.model import AnilistCache, AnimeMedia, ListEntry, MediaListStatus
from rui.common import config, persistence

logger = logging.getLogger(__name__)


def getWatchingListByUsername(username) -> List[ListEntry]:
    return getListByUsernameAndStatus(username, MediaListStatus.CURRENT)


def getCompletedListByUsername(username) -> List[ListEntry]:
    return getListByUsernameAndStatus(username, MediaListStatus.COMPLETED)


def getPlanningCustomList(username, custom_list_name) -> List[ListEntry]:
    return [
        anime
        for anime in getListByUsernameAndStatus(username, MediaListStatus.PLANNING)
        if custom_list_name.lower() in anime.customLists
    ]


def getListEntryByAnimeId(username, anime_id) -> ListEntry:
    """Returns the ListEntry for a given anime_id and username."""

    logger.debug(f"Searching list entry for anime_id {anime_id} in completed list.")
    entries = [e for e in getCompletedListByUsername(username) if e.id == anime_id]

    if entries:
        return entries[0]

    logger.debug(f"Searching list entry for anime_id {anime_id} in watching list.")
    entries = [e for e in getWatchingListByUsername(username) if e.id == anime_id]

    if entries:
        return entries[0]

    logger.debug(f"Searching list entry for anime_id {anime_id} in planning list.")
    entries = [
        e
        for e in getListByUsernameAndStatus(username, MediaListStatus.PLANNING)
        if e.id == anime_id
    ]

    if entries:
        return entries[0]

    return None


def _wait_request_limit() -> None:
    request_interval = config.get("anilist.requestInterval") or 2

    if not persistence.get("anilist"):
        persistence.set("anilist", {})

    last_request = persistence.get("anilist").get("last_request")
    if last_request:
        last_request = datetime.strptime(
            persistence.get("anilist")["last_request"], "%Y-%m-%d %H:%M:%S"
        )

    while last_request and (datetime.now() - last_request) <= timedelta(
        seconds=request_interval
    ):
        logger.debug("Waiting for request interval.")
        sleep(1)

    persistence.set(
        "anilist", {"last_request": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    )


def getListByUsernameAndStatus(username, status) -> List[ListEntry]:
    cache_key = f"{username}-{status}"
    cache = AnilistCache.getCache(cache_key)

    if config.get("cache.enabled") and cache:
        logger.info("Getting watching list from cache.")
        entries = cache
    else:
        _wait_request_limit()
        response = requests.post(
            query.ENDPOINT,
            json={
                "query": query.LIST_BY_USERNAME_AND_STATUS,
                "variables": {"username": username, "status": status},
            },
        ).json()
        entries = (
            response.get("data")
            .get("MediaListCollection")
            .get("lists")[0]
            .get("entries")
        )
        logger.debug("Raw response: " + json.dumps(entries, indent=2))

        if config.get("cache.enabled"):
            AnilistCache.writeCache(cache_key, entries)

    rtn = []
    for entry in entries:
        rtn.append(ListEntry(entry))

    logger.debug("Mapped respose: " + str(rtn))
    return rtn


def getAnimeById(anime_id):
    cache_key = f"anime-{anime_id}"
    cache = AnilistCache.getCache(cache_key)

    if config.get("cache.enabled") and cache:
        logger.info(f"Getting anime {anime_id} from cache.")
        response = cache
    else:
        _wait_request_limit()
        response = requests.post(
            query.ENDPOINT,
            json={"query": query.MEDIA_BY_ID, "variables": {"id": anime_id}},
        ).json()

        if config.get("cache.enabled"):
            AnilistCache.writeCache(cache_key, response)

    return AnimeMedia(response["data"]["Media"])


def searchAnime(search_string: str):
    cache_key = f"search-{search_string}"
    cache = AnilistCache.getCache(cache_key)
    excluded_formats = ["MUSIC", "MANGA", "NOVEL", "ONE_SHOT"]

    if config.get("cache.enabled") and cache:
        logger.info(f"Getting search results for '{search_string}' from cache.")
        response = cache
    else:
        _wait_request_limit()
        response = requests.post(
            query.ENDPOINT,
            json={
                "query": query.MEDIA_SEARCH,
                "variables": {"search": search_string},
                "format_not_in": excluded_formats,  # doesn't works..
            },
        ).json()

        if config.get("cache.enabled"):
            AnilistCache.writeCache(cache_key, response)

    return [
        AnimeMedia(r)
        for r in response["data"]["Page"]["media"]
        if r["format"] not in excluded_formats
    ]
