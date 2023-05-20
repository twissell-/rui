import logging
from rich import print

from core import fileManager, anilist, config, selector, animebytes
from core.anilist import MediaStatus
from core.torrentClient import TorrentClient, QBitTorrentClient
from core import persistence


def load_current(dry_run: bool, id_: int):
    """Searchs torrents for new episodes for each anime in watching list and add them to qBitTorrent."""

    logger = logging.getLogger(__name__)
    animes = []

    if config.get("torrentLoader.lists.watching"):
        animes += anilist.getWatchingListByUsername(config.get("anilist.username"))

    if config.get("torrentLoader.lists.customPlanning"):
        animes += anilist.getPlanningCustomList(
            config.get("anilist.username"),
            config.get("torrentLoader.lists.customPlanning"),
        )

    animes = [
        anime
        for anime in animes
        if anime.airingStatus in [MediaStatus.RELEASING, MediaStatus.FINISHED]
    ]

    output = []
    for anime in animes:
        logger.info("-" * 120)

        if anime.notes and "rui.ignore" in anime.notes:
            continue

        if id_ and anime.id != int(id_):
            continue

        output.append("=" * 120)
        output.append("Anime:%s" % anime)
        output.append("Destination: %s" % fileManager.getDestinationPath(anime))

        missingEpisodes = fileManager.getMissingEpisodes(anime)
        if not missingEpisodes:
            output.append("All episodes of %s have been downloaded." % anime.title)
            continue

        output.append("Missing Episodes: %s" % missingEpisodes)

        collection = selector.selectCollection(
            anime, animebytes.getTorrentCollectionByAnime(anime)
        )
        if not collection:
            logger.info('No torrent collection found for "%s"' % anime.title)
            output.append('No torrent collection found for "%s"' % anime.title)
            continue

        output.append("Collection: %s" % collection)

        torrents = selector.selectTorrentFromCollection(
            anime, collection, missingEpisodes
        )
        if not torrents:
            output.append(
                'No torrents found for "%s" %s' % (anime.title, str(missingEpisodes))
            )
            continue

        # tc = TorrentClient()
        tc = QBitTorrentClient()
        for torrent in torrents:
            output.append("Torrent: %s" % torrent)
            if not dry_run:
                if torrent.episode:
                    detail = " - %03d" % torrent.episode
                elif anime.episodes > 1:
                    detail = " - %03d-%03d" % (anime.firstEpisode, anime.lastEpisode)
                else:
                    detail = ""

                name = anime.title + detail
                category = "Anime"
                tags = ",".join(
                    ["rui-ng", "Ongoing" if torrent.episode else "Finished"]
                )
                tc.add(
                    torrent.url,
                    fileManager.getDestinationPath(anime, True),
                    name=name,
                    category=category,
                    tags=tags,
                )

                anime_data = persistence.get(anime.id)
                if not anime_data.get("loaded_episodes"):
                    anime_data["loaded_episodes"] = [torrent.episode]
                else:
                    anime_data.get("loaded_episodes").append(torrent.episode)

                persistence.set(anime.id, anime_data)

    for line in output:
        print(line)
