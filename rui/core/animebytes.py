import requests
import json
import logging
from core import config
from core.common import MediaFormat
from pprint import pprint

logger = logging.getLogger(__name__)

_ENDPOINT = 'https://animebytes.tv/scrape.php?torrent_pass={torrentPass}&format=anime&username={username}&searchstr={searchstr}&filter_cat%5B1%5D&type=anime'


def getTorrentCollectionByAnime(anime):
    return getTorrentCollectionByTitle(anime.romaji) or getTorrentCollectionByTitle(anime.english) 


def getTorrentCollectionByTitle(title):
    logger.info('Getting torrents list for "%s"' % title)
    response = requests.get(_ENDPOINT.format(
            torrentPass=config.get('animebytes.torrentPass'),
            username=config.get('animebytes.username'),
            searchstr=title
        )).json()
    logger.debug('Raw response: ' + str(response))


    if response.get('Matches') == 0:
        logger.info('No results found.')
        return []

    rtn = []
    for anime in response.get('Groups'):
        rtn.append(TorrentCollection(anime))

    logger.debug('Mapped respose: ' + str(rtn))
    return rtn


class TorrentCollection(object):
    def __init__(self, raw_collection):
        super(TorrentCollection, self).__init__()
        self._seriesName = raw_collection.get('SeriesName')
        self._format = MediaFormat.map(raw_collection.get('GroupName'))
        self._year = int(raw_collection.get('Year'))
        self._torrents = []

        for torrent in raw_collection.get('Torrents'):
            self._torrents.append(Torrent(torrent))

        self._selectorScore = -1000

    @property
    def title(self):
        return self._seriesName

    @property
    def format(self):
        return self._format

    @property
    def year(self):
        return self._year

    @property
    def torrents(self):
        return self._torrents

    @property
    def score(self):
        return self._selectorScore

    @score.setter
    def score(self, value):
        self._selectorScore = value

    def __repr__(self):
        return '%s (%s) [%s] - %d torrents' % (self.title, self.format.name, self.year, len(self.torrents))



class Torrent(object):
    def __init__(self, raw_torrent):
        super(Torrent, self).__init__()
        self._url = raw_torrent.get('Link')
        self._properties = raw_torrent.get('Property')
        self._rawDownMultiplier = raw_torrent.get('RawDownMultiplier')
        self._rawUpMultiplier = raw_torrent.get('RawUpMultiplier')
        self._seeders = raw_torrent.get('Seeders')
        self._leechers = raw_torrent.get('Leechers')

        raw_episode = raw_torrent.get('EditionData').get('EditionTitle')
        if not raw_episode:
            self._episode = 0
        else:
            self._episode = int(''.join(i for i in raw_episode if i.isdigit()))

        self._selectorScore = 0


    @property
    def url(self):
        return self._url

    @property
    def properties(self):
        return self._properties

    @property
    def rawDownMultiplier(self):
        return self._rawDownMultiplier

    @property
    def rawUpMultiplier(self):
        return self._rawUpMultiplier

    @property
    def seeders(self):
        return self._seeders

    @property
    def leechers(self):
        return self._leechers

    @property
    def episode(self):
        return self._episode

    @property
    def score(self):
        return self._selectorScore

    @score.setter
    def score(self, value):
        self._selectorScore = value

    def __repr__(self):
        return '%s - %s (S: %s | L: %s)' % (self.episode, self.properties, self.seeders, self.leechers)
