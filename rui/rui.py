#!/usr/bin/env python3

import logging
from logging.handlers import RotatingFileHandler
import commands
import typer

root_logger = logging.getLogger("")
root_logger.setLevel(logging.DEBUG)

log_handler = logging.handlers.RotatingFileHandler("./rui.log", backupCount=3)
log_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)
root_logger.addHandler(log_handler)
log_handler.doRollover()

app = typer.Typer()


@app.command(
    help="Searchs torrents for new episodes for each anime in watching list and add them to qBitTorrent."
)
def load(
    dry_run: bool = typer.Option(False, help="Do not add the torrent to transmission."),
    id: int = typer.Option(
        0, help="Process only anime with the given anilist id. Useful for debug."
    ),
    verbose: bool = typer.Option(False),
):
    if verbose:
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(logging.Formatter("[%(levelname)s]: %(message)s"))
        log_handler.setLevel(logging.INFO)
        root_logger.addHandler(log_handler)

    commands.load_current(dry_run, id)


@app.command(help="Creates a spec file for a given anime.")
def spec(anime_id: int):
    # animes = anilist.getCompletedListByUsername('demo')
    # for anime in animes:
    #     commands.spec(anime.id)
    #
    commands.spec(anime_id)


if __name__ == "__main__":
    app()
