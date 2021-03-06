import requests
import json
import logging
import os
from glob import glob
from datetime import datetime

from core.common import MediaFormat
from core import config

logger = logging.getLogger(__name__)

class MediaListStatus(object):
    CURRENT = 'CURRENT'
    PLANNING = 'PLANNING'
    COMPLETED = 'COMPLETED'
    DROPPED = 'DROPPED'
    PAUSED = 'PAUSED'
    REPEATING = 'REPEATING'

_QUERY = '''
query ($username: String, $status: MediaListStatus) {
  MediaListCollection(userName: $username, type: ANIME, status: $status) {
    lists {
      name
      status
      entries {
        score
        media {
          id
          title {
            english
            romaji
            userPreferred
          }
          episodes
          format
          startDate {
            year
          }
          endDate {
            year
          }
        }
        progress
        notes
      }
    }
  }
}
'''
_ENDPOINT = 'https://graphql.anilist.co'

def getWatchingListByUsername(username):
    return getListByUsernameAndStatus(username, MediaListStatus.CURRENT)


def getCompletedListByUsername(username):
    return getListByUsernameAndStatus(username, MediaListStatus.COMPLETED)


def getListByUsernameAndStatus(username, status):

    cache = AnilistCache.getCache(username, status)
    if config.get('cache.enabled') and cache:
        logger.info('Getting watching list from cache.')
        entries = cache
    else:
        response = requests.post(
                _ENDPOINT,
                json = {
                    'query': _QUERY,
                    'variables': {
                        'username': username,
                        'status': status
                    }
                }).json()
        entries = response.get('data').get('MediaListCollection').get('lists')[0].get('entries')
        logger.debug('Raw response: ' + str(entries))

        if config.get('cache.enabled'):
            AnilistCache.writeCache(username, status, entries)

    rtn = []
    for entry in entries:
        rtn.append(ListEntry(entry))

    logger.debug('Mapped respose: ' + str(rtn))
    return rtn


class AnilistCache(object):

    @staticmethod
    def _getCacheFilePath(username, status):
        return os.path.join(config.get('downloads.tmpdir'), 'rui-%s-%s.cache' % (username, status))
    
    @staticmethod
    def getCache(username, status):
        cachePath = AnilistCache._getCacheFilePath(username, status)
        now = datetime.now().timestamp()

        try:
            cacheFile = open(cachePath)
            cache = json.load(cacheFile)

            cacheLifetime = (now - cache.get('ts')) / 60
            if cacheLifetime > config.get('cache.expiration'):
                return False

        except OSError as err:
            return False
        except json.JSONDecodeError as err:
            return False
        else:
            return cache.get('data')

    @staticmethod
    def writeCache(username, status, data):
        cachePath = AnilistCache._getCacheFilePath(username, status)
        ts = datetime.now().timestamp()

        with open(cachePath, 'w') as cacheFile:
            json.dump({
                'ts': ts,
                'data': data
            }, cacheFile)
        logger.info('Cache "%s" updated. ts: %f' % (cachePath, ts))

    @staticmethod
    def clearCache():
        cachePath = AnilistCache._getCacheFilePath('*', '*')

        fileList = glob(cachePath)
        for filePath in fileList:
            os.remove(filePath)
            logger.info("Deleted file : %s" % filePath)


class ListEntry(object):
    def __init__(self, raw_entry):
        super(ListEntry, self).__init__()
        self._id = self._title = raw_entry.get('media').get('id')
        self._title = raw_entry.get('media').get('title').get('userPreferred')
        self._english = raw_entry.get('media').get('title').get('english')
        self._romaji = raw_entry.get('media').get('title').get('romaji')
        self._progress = raw_entry.get('progress')
        self._notes = raw_entry.get('notes')
        self._episodes = raw_entry.get('media').get('episodes') or 99
        self._format = MediaFormat.map(raw_entry.get('media').get('format'))
        self._startYear = raw_entry.get('media').get('startDate').get('year')
        self._endYear = raw_entry.get('media').get('endDate').get('year')
        self._score = raw_entry.get('score') or 0

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
    def progress(self):
        return self._progress

    @property
    def notes(self):
        return self._notes

    @property
    def episodes(self):
        return self._episodes

    @property
    def year(self):
        return self._startYear

    @property
    def format(self):
        return self._format

    @property
    def score(self):
        return self._score

    @property
    def ongoing(self):
        if self._endYear:
            return False
        else:
            return True

    def __repr__(self):
        return '[%d] %s (%d/%d) %s' % (self.id, self.title, self.progress or 0, self.episodes or 0, 'Ongoing' if self.ongoing else 'Finished')

    def __lt__(self, other):
        return self.title < other.title


