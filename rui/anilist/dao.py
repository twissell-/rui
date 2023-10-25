import json
import logging
from typing import List

import requests

from rui.anilist import query
from rui.anilist.model import AnilistCache, ListEntry, MediaListStatus
from rui.common import config

logger = logging.getLogger(__name__)


def getWatchingListByUsername(username):
    return getListByUsernameAndStatus(username, MediaListStatus.CURRENT)


def getCompletedListByUsername(username):
    return getListByUsernameAndStatus(username, MediaListStatus.COMPLETED)


def getPlanningCustomList(username, custom_list_name):
    return [
        anime
        for anime in getListByUsernameAndStatus(username, MediaListStatus.PLANNING)
        if custom_list_name.lower() in anime.customLists
    ]


def getListByUsernameAndStatus(username, status):
    cache = AnilistCache.getCache(username, status)
    if config.get("cache.enabled") and cache:
        logger.info("Getting watching list from cache.")
        entries = cache
    else:
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
            AnilistCache.writeCache(username, status, entries)

    rtn = []
    for entry in entries:
        rtn.append(ListEntry(entry))

    logger.debug("Mapped respose: " + str(rtn))
    return rtn


def getAnimeSpecById(anime_id):
    response = requests.post(
        query.ENDPOINT,
        json={"query": query.MEDIA_BY_ID, "variables": {"id": anime_id}},
    ).json()

    return response["data"]["Media"]


def getCompletedAnimes(since: str) -> List[dict]:
    response = requests.post(
        query.ENDPOINT,
        json={
            "query": query.COMPLETED_BY_USERNAME_AND_SINCE,
            "variables": {
                "username": config.get("anilist_todoist.username"),
                "status": "COMPLETED",
                "since": since,
            },
        },
    ).json()

    lists = response["data"]["MediaListCollection"]["lists"]
    if not lists:
        return []

    return response["data"]["MediaListCollection"]["lists"][0]["entries"]
