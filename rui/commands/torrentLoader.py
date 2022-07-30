import logging

from core import (
    fileManager,
    anilist,
    config,
    selector,
    animebytes
)
from core.torrentClient import TorrentClient, QBitTorrentClient


def load_current(dry_run: bool, id_: int):
    """Searchs torrents for new episodes for each anime in watching list and add them to qBitTorrent."""

    logger = logging.getLogger(__name__)
    output = []

    for anime in anilist.getWatchingListByUsername(config.get('anilist.username')):
        logger.info('=' * 120)

        if anime.notes and 'rui.ignore' in anime.notes:
            continue

        if id_ and anime.id != int(id_):
            continue

        output.append('=' * 120)
        output.append('Anime:%s' % anime)
        output.append('Destination: %s' % fileManager.getDestinationPath(anime, True))

        missingEpisodes = fileManager.getMissingEpisodes(anime)
        if not missingEpisodes:
            output.append('All episodes of %s have been downloaded.' % anime.title)
            continue

        output.append('Missing Episodes: %s' % missingEpisodes)

        collection = selector.selectCollection(anime, animebytes.getTorrentCollectionByAnime(anime))
        if not collection:
            output.append('No torrent collection found for "%s"' % anime.title)
            continue

        output.append('Collection: %s' % collection)

        torrents = selector.selectTorrentFromCollection(anime, collection, missingEpisodes)
        if not torrents:
            output.append('No torrents found for "%s" %s' % (anime.title, str(missingEpisodes)))
            continue

        # tc = TorrentClient()
        tc = QBitTorrentClient()
        for torrent in torrents:
            output.append('Torrent: %s' % torrent)
            if not dry_run:
                if torrent.episode:
                    detail = ' - %03d' % torrent.episode
                elif anime.episodes > 1:
                    detail = ' - %03d-%03d' % (anime.firstEpisode, anime.lastEpisode)
                else:
                    detail = ''

                name = anime.title + detail
                category = 'Anime'
                tags = ','.join(['rui', 'Ongoing' if torrent.episode else 'Finished'])
                tc.add(
                    torrent.url, fileManager.getDestinationPath(anime, True),
                    name=name, category=category, tags=tags)

    for line in output:
        logger.info(line)
