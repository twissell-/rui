#!/usr/bin/env python3

import logging
import argparse
from logging.handlers import RotatingFileHandler

from core import (
    anilist,
    animebytes,
    selector,
    fileManager,
    config
)
from core.torrentClient import TorrentClient
import commands
from pprint import pprint

root_logger = logging.getLogger('')
root_logger.setLevel(logging.INFO)

loghandler = logging.handlers.RotatingFileHandler(
    './rui.log', maxBytes=10 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s - %(name)s ln.%(lineno)d - %(message)s')

loghandler.setFormatter(formatter)
root_logger.addHandler(loghandler)

logger = logging.getLogger('cli')


parser = argparse.ArgumentParser(prog='rui', add_help=True)
subparsers = parser.add_subparsers()

for name in dir(commands):
    if not (name[-2:] == '__' or name == 'command'):
        command_class = getattr(commands, name)
        if issubclass(command_class, commands.command.Command):
            command = command_class()
            command.configureParameters(subparsers.add_parser(name[0].lower() + name[1:])).set_defaults(func=command.execute)


def main(parser):
    args = parser.parse_args()
    if 'func' in dir(args):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main(parser)
