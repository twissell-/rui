import json
import logging
import os
from datetime import datetime, timedelta
from glob import glob

from rui.common import config, persistence
from rui.common.utils import MediaFormat

logger = logging.getLogger(__name__)


class MediaListStatus:
    CURRENT = "CURRENT"
    PLANNING = "PLANNING"
    COMPLETED = "COMPLETED"
    DROPPED = "DROPPED"
    PAUSED = "PAUSED"
    REPEATING = "REPEATING"


class MediaStatus:
    FINISHED = "FINISHED"
    RELEASING = "RELEASING"
    NOT_YET_RELEASED = "NOT_YET_RELEASED"
    CANCELLED = "CANCELLED"
    HIATUS = "HIATUS"


class AnilistCache(object):
    @staticmethod
    def _getCacheFilePath():
        return os.path.join(config.get("torrentLoader.tmpdir"), "rui.cache")

    @staticmethod
    def getCache(cache_key: str) -> dict | None:
        cachePath = AnilistCache._getCacheFilePath()
        # now = datetime.now().timestamp()

        cache = persistence.get(cache_key, path=cachePath)

        if not cache:
            return False

        if not cache.get("_last_update"):
            return False

        last_update = datetime.strptime(cache["_last_update"], "%Y-%m-%d %H:%M:%S")

        if (datetime.now() - last_update) > timedelta(
            seconds=config.get("cache.expiration")
        ):
            return False

        return cache.get("data")

    @staticmethod
    def writeCache(cache_key: str, data: dict) -> None:
        cachePath = AnilistCache._getCacheFilePath()

        persistence.set(cache_key, {"data": data}, path=cachePath, indent=None)

        logger.info(f'Cache "{cache_key}" updated.')
        return

        with open(cachePath, "w") as cacheFile:
            json.dump({"data": data}, cacheFile)

    @staticmethod
    def clearCache():
        cachePath = AnilistCache._getCacheFilePath()

        fileList = glob(cachePath)
        for filePath in fileList:
            os.remove(filePath)
            logger.info("Deleted file : %s" % filePath)


class AnimeMedia(object):
    def __init__(self, raw_media):
        super(AnimeMedia, self).__init__()
        self.id = raw_media.get("id")
        self.title = config.get(
            "valueOverride." + str(self.id) + ".title"
        ) or raw_media.get("title").get("userPreferred")
        self.english = raw_media.get("title").get("english")
        self.romaji = raw_media.get("title").get("romaji")
        self.native = raw_media.get("title").get("native")
        self.episodes = raw_media.get("episodes") or 98
        self.duration = raw_media.get("duration")
        self.firstEpisode = (
            config.get("valueOverride." + str(self.id) + ".firstEpisode") or 1
        )
        self.format = MediaFormat.map(raw_media.get("format"))
        self.startYear = raw_media.get("startDate").get("year")
        self.endYear = raw_media.get("endDate").get("year")
        self.season = raw_media.get("season")
        self.status = raw_media.get("status")
        self.source = raw_media.get("source")
        self.searchString = config.get(
            "valueOverride." + str(self.id) + ".searchString"
        )
        self.converImage = raw_media.get("coverImage").get("extraLarge")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "titles": {
                "english": self.english,
                "romaji": self.romaji,
                "native": self.native,
            },
            "episodes": self.episodes,
            "duration": self.duration,
            "firstEpisode": self.firstEpisode,
            "format": self.format.name,
            "startYear": self.startYear,
            "endYear": self.endYear,
            "season": self.season,
            "status": self.status,
            "source": self.source,
            "converImage": self.converImage,
        }

    def __repr__(self):
        return "[%d] %s %s %d %s" % (
            self.id,
            self.title,
            self.format.name,
            self.startYear,
            self.status,
        )

    @property
    def lastEpisode(self):
        return self.firstEpisode + self.episodes - 1


class ListEntry(object):
    def __init__(self, raw_entry):
        super(ListEntry, self).__init__()
        self._id = raw_entry.get("media").get("id")
        self._title = config.get(
            "valueOverride." + str(self._id) + ".title"
        ) or raw_entry.get("media").get("title").get("userPreferred")
        self._english = raw_entry.get("media").get("title").get("english")
        self._romaji = raw_entry.get("media").get("title").get("romaji")
        self._native = raw_entry.get("media").get("title").get("native")
        self._progress = raw_entry.get("progress")
        self._notes = raw_entry.get("notes")
        self._episodes = raw_entry.get("media").get("episodes") or 98
        self._firstEpisode = (
            config.get("valueOverride." + str(self._id) + ".firstEpisode") or 1
        )
        self._format = MediaFormat.map(raw_entry.get("media").get("format"))
        self._startYear = raw_entry.get("media").get("startDate").get("year")
        self._endYear = raw_entry.get("media").get("endDate").get("year")
        self._airingStatus = raw_entry.get("media").get("status")
        self._customLists = [
            key for key, value in raw_entry.get("customLists").items() if value
        ]
        self._score = raw_entry.get("score") or 0
        self._searchString = config.get(
            "valueOverride." + str(self._id) + ".searchString"
        )
        if raw_entry.get("completedAt").get("year"):
            self.completedAt = datetime(
                raw_entry.get("completedAt").get("year"),
                raw_entry.get("completedAt").get("month", 1),
                raw_entry.get("completedAt").get("day", 1),
            )
        else:
            self.completedAt = None

    @property
    def id(self):
        return self._id

    @property
    def title(self):
        return self._title

    @property
    def english(self):
        return self._english

    @property
    def romaji(self):
        return self._romaji

    @property
    def native(self):
        return self._native

    @property
    def progress(self):
        return self._progress

    @property
    def notes(self):
        return self._notes

    @property
    def episodes(self):
        return self._episodes

    @property
    def firstEpisode(self):
        return self._firstEpisode

    @property
    def lastEpisode(self):
        return self.firstEpisode + self.episodes - 1

    @property
    def year(self):
        return self._startYear

    @property
    def format(self):
        return self._format

    @property
    def airingStatus(self):
        return self._airingStatus

    @property
    def score(self):
        return self._score

    @property
    def customLists(self):
        return self._customLists

    @property
    def ongoing(self):
        if self.airingStatus == MediaStatus.RELEASING:
            return True
        else:
            return False

    @property
    def searchString(self):
        return self._searchString

    def __repr__(self):
        return "[%d] %s (%d/%d) %s" % (
            self.id,
            self.title,
            self.progress or 0,
            self.episodes or 0,
            "Ongoing" if self.ongoing else "Finished",
        )

    def __lt__(self, other):
        return self.title < other.title
