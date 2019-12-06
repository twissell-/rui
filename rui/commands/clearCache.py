
from .command import (
    Command,
    CommandOutput,
)
from core.anilist import AnilistCache

class ClearCache(Command):
    """Searchs torrents for new episodes for each anime in watching list and add them to transmission."""

    def configureParameters(self, parser):
        super().configureParameters(parser)
        parser.description = 'Deletes all cache files.'

        return parser

    def _execute(self, args):
        AnilistCache.clearCache()

        return CommandOutput()
