#!/usr/bin/env python3

import logging
import argparse
import inspect
from logging.handlers import RotatingFileHandler

from core import (
    anilist,
    animebytes,
    selector,
    fileManager,
    config
)
from core.torrentClient import TorrentClient, QBitTorrentClient
import commands
from pprint import pprint

root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)

loghandler = logging.handlers.RotatingFileHandler(
    './rui.log', maxBytes=100 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s - %(name)s ln.%(lineno)d - %(message)s')

loghandler.setFormatter(formatter)
root_logger.addHandler(loghandler)

logger = logging.getLogger('cli')

def main():
    parser = argparse.ArgumentParser(prog='rui', add_help=True)
    subparsers = parser.add_subparsers()

    for name in dir(commands):
        if not (name[-2:] == '__' or name == 'command'):
            command_class = getattr(commands, name)
            if inspect.ismodule(command_class):
                continue

            if issubclass(command_class, commands.command.Command):
                command = command_class()
                command.configureParameters(subparsers.add_parser(name[0].lower() + name[1:])).set_defaults(func=command.execute)

    args = parser.parse_args()
    if 'func' in dir(args):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        logger.error(err, exc_info=True)
        exit(1)
