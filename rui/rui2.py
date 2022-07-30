#!/usr/bin/env python3

import logging
from logging.handlers import RotatingFileHandler
import commands
import typer

root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)

loghandler = logging.handlers.RotatingFileHandler('./rui.log', maxBytes=100 * 1024, backupCount=2)
loghandler.setFormatter(
    logging.Formatter('%(asctime)s %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
root_logger.addHandler(loghandler)

app = typer.Typer()


@app.command(
    help='Searchs torrents for new episodes for each anime in watching list and add them to qBitTorrent.'
)
def load(
    dry_run: bool = typer.Option(False, help='Do not add the torrent to transmission.'),
    id: int = typer.Option(0, help='Process only anime with the given anilist id. Useful for debug.'),
    verbose: bool = typer.Option(False)
):
    if verbose:
        loghandler = logging.StreamHandler()
        loghandler.setFormatter(logging.Formatter('[%(levelname)s]: %(message)s'))
        loghandler.setLevel(logging.INFO)
        root_logger.addHandler(loghandler)

    commands.load_current(dry_run, id)


@app.command()
def other(dry_run: bool):
    print(f"Hello")


if __name__ == '__main__':
    app()
