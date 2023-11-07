import json
import logging
import os
from datetime import datetime
from glob import glob

from rui.common import config
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
    def _getCacheFilePath(username, status):
        return os.path.join(
            config.get("torrentLoader.tmpdir"), "rui-%s-%s.cache" % (username, status)
        )

    @staticmethod
    def getCache(username, status):
        cachePath = AnilistCache._getCacheFilePath(username, status)
        now = datetime.now().timestamp()

        try:
            cacheFile = open(cachePath)
            cache = json.load(cacheFile)

            cacheLifetime = (now - cache.get("ts")) / 60
            if cacheLifetime > config.get("cache.expiration"):
                return False

        except OSError as err:
            return False
        except json.JSONDecodeError as err:
            return False
        else:
            return cache.get("data")

    @staticmethod
    def writeCache(username, status, data):
        cachePath = AnilistCache._getCacheFilePath(username, status)
        ts = datetime.now().timestamp()

        with open(cachePath, "w") as cacheFile:
            json.dump({"ts": ts, "data": data}, cacheFile)
        logger.info('Cache "%s" updated. ts: %f' % (cachePath, ts))

    @staticmethod
    def clearCache():
        cachePath = AnilistCache._getCacheFilePath("*", "*")

        fileList = glob(cachePath)
        for filePath in fileList:
            os.remove(filePath)
            logger.info("Deleted file : %s" % filePath)


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
