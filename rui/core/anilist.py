import requests
import json
import logging

from core.common import MediaFormat

logger = logging.getLogger(__name__)

_QUERY = '''
query ($username: String) {
  MediaListCollection(userName: $username, type: ANIME, status: CURRENT) {
    lists {
      name
      status
      entries {
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
    logger.info('Getting watching list.')
    response = requests.post(
            _ENDPOINT,
            json={'query': _QUERY, 'variables': {'username': username}}).json()

    entries = response.get('data').get('MediaListCollection').get('lists')[0].get('entries')
    logger.debug('Raw response: ' + str(entries))

    rtn = []
    for entry in entries:
        rtn.append(ListEntry(entry))

    logger.debug('Mapped respose: ' + str(rtn))
    return rtn


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
    def ongoing(self):
        if self._endYear:
            return False
        else:
            return True

    def __repr__(self):
        return '[%d] %s (%d/%d) %s' % (self.id, self.title, self.progress or 0, self.episodes or 0, 'Ongoing' if self.ongoing else 'Finished')


