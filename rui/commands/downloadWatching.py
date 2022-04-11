
from .command import (
    Command,
    CommandOutput,
)
from core import (
    fileManager,
    anilist,
    config,
    selector,
    animebytes
)
from core.torrentClient import TorrentClient, QBitTorrentClient



class DownloadWatching(Command):
    """Searchs torrents for new episodes for each anime in watching list and add them to transmission."""

    def configureParameters(self, parser):
        super().configureParameters(parser)
        parser.description = 'Searchs torrents for new episodes for each anime in watching list and add them to transmission.'
        parser.add_argument('--dry-run', action='store_true', help='Do not add the torrent to transmission.')
        parser.add_argument('--id', action='store', default=False, help='Process only anime with the given anilist id. Useful for debug.')

        return parser

    def _execute(self, args):
    # def process(isDryRun=False, verbose=False):
        output = ''
        for anime in anilist.getWatchingListByUsername(config.get('anilist.username')):
            if anime.notes and 'rui.ignore' in anime.notes:
                continue
            if args.id and anime.id != int(args.id):
                continue
            if args.verbose: 
                output += ('=' * 120 + '\n')
                output += ('Anime:%s' % anime + '\n')
                output += ('Destination: %s' % fileManager.getDestinationPath(anime, True) + '\n')

            missingEpisodes = fileManager.getMissingEpisodes(anime)
            if not missingEpisodes:
                if args.verbose: output += ('All episodes of %s have been downloaded.\n' % anime.title)
                continue
            if args.verbose: output += ('Missing Episodes: %s' % missingEpisodes + '\n')

            collection = selector.selectCollection(anime, animebytes.getTorrentCollectionByAnime(anime))
            if not collection:
                if args.verbose: output += ('No torrent collection found for "%s"' % anime.title + '\n')
                continue
            if args.verbose: output += ('Collection: %s' % collection + '\n')

            torrents = selector.selectTorrentFromCollection(anime, collection, missingEpisodes)
            if not torrents:
                if args.verbose: output += ('No torrents found for "%s" %s' % (anime.title, str(missingEpisodes)) + '\n')
                continue

            #tc = TorrentClient()
            tc = QBitTorrentClient()
            for torrent in torrents:
                if args.verbose: output += ('Torrent: %s' % torrent + '\n')
                if not args.dry_run:
                    tc.add(torrent.url, fileManager.getDestinationPath(anime, True))

        return CommandOutput(exit_status=0, message=output)
