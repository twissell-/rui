import os
from tabulate import tabulate

from .command import (
    Command,
    CommandOutput,
)

from core.common import sanitize
from core import (
    fileManager,
    anilist,
    config
)


class Report(Command):
    """Searchs torrents for new episodes for each anime in watching list and add them to transmission."""

    def configureParameters(self, parser):
        super().configureParameters(parser)
        parser.description = 'Reports over your anime collection.'
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--missing-anime', action='store_true', help='List completed and not downloaded Anime with score above or equal "reports.saveMinimunScore"')
        group.add_argument('--anime-to-purge', action='store_true', help='List downloaded Anime with score below "reports.saveMinimunScore"')
        group.add_argument('--destination', action='store_true', help='List all completed anime and where its/should be downloaded')

        return parser

    def _misingAnimeReport(self, args):
        headers= [
            'ID',
            'Title',
            'Score',
            'Location',
            "Missing"
        ]
        output = []
        animeToCheck = [anime for anime in anilist.getCompletedListByUsername(config.get('anilist.username')) if anime.score >= config.get('reports.saveMinimunScore')]

        for anime in sorted(animeToCheck):
            searchDirs = [fileManager.getDestinationPath(anime)]
            searchDirs += [fileManager.getDestinationPath(anime, basePath=dir_) for dir_ in config.get('reports.alternativeDirecories')]

            row = []
            for dir_ in searchDirs:
                missingEpisodes = fileManager.getMissingEpisodes(anime, dir_)
                if not missingEpisodes:
                    row = []
                    break
                else:
                    row = [anime.id, anime.title, anime.score]
                    row.append(dir_)
                    if len(missingEpisodes) > 12:
                        row.append(str(missingEpisodes[:12]) + '+')
                    else:
                        row.append(missingEpisodes)

            if row: output.append(row)

        return CommandOutput(exit_status=0, message=(output, headers))

    def _animeToPurgeReport(self, args):
        headers= [
            'ID',
            'Title',
            'Score',
            'Location',
            "Episodes"
        ]
        output = []
        animeToCheck = [anime for anime in anilist.getCompletedListByUsername(config.get('anilist.username')) if anime.score < config.get('reports.saveMinimunScore')]

        for anime in sorted(animeToCheck):
            searchDirs = [fileManager.getDestinationPath(anime)]
            searchDirs += [fileManager.getDestinationPath(anime, basePath=dir_) for dir_ in config.get('reports.alternativeDirecories')]

            for dir_ in searchDirs:
                episodes = fileManager.getEpisodes(anime, dir_)
                if episodes:
                    row = [anime.id, anime.title, anime.score]
                    row.append(dir_)
                    row.append(len(episodes))
                    output.append(row)


        return CommandOutput(exit_status=0, message=(output, headers))

    def _destinationReport(self, args):
        headers= [
            'ID',
            'Title',
            'Score',
            'Destination',
            "Episodes"
        ]
        output = []

        for anime in sorted(anilist.getCompletedListByUsername(config.get('anilist.username'))):
            searchDirs = [fileManager.getDestinationPath(anime)]
            searchDirs += [fileManager.getDestinationPath(anime, basePath=dir_) for dir_ in config.get('reports.alternativeDirecories')]

            row = [anime.id, anime.title, anime.score]
            destination = fileManager.getDestinationPath(anime)
            episodeCount = 0
            for dir_ in searchDirs:
                episodes = fileManager.getEpisodes(anime, dir_)
                if episodes:
                    destination = dir_
                    episodeCount = len(episodes)

            row.append(destination)
            row.append(episodeCount)
            output.append(row)

        return CommandOutput(exit_status=0, message=(output, headers))


    def _execute(self, args):
        if args.missing_anime:
            return self._misingAnimeReport(args)
        if args.anime_to_purge:
            return self._animeToPurgeReport(args)
        if args.destination:
            return self._destinationReport(args)

        return CommandOutput(exit_status=1, message='No report selected')

    def _formatOutput(self, output):
        if output.exit_status == 1:
            print(output.message)
        else:
            print(tabulate(*output.message, tablefmt="psql"))

