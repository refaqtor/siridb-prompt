#!/usr/bin/python3
'''SiriDB Prompt

SiriDB Prompt can be used to manage, query, or insert data into a SiriDB
database.

:copyright: 2016, Jeroen van der Heijden (Transceptor Technology)
'''
import sys
import argparse
import asyncio
import logging
import re
import signal
import encodings.idna  # fixes idna encoding error
from prompt_toolkit import prompt
from siridb.connector import SiriDBClient
from lib.ploop import prompt_loop, force_exit
from lib.version import __email__
from lib.version import __maintainer__
from lib.version import __version__
from lib.utils import get_hostlist


def signal_handler(*args):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        if force_exit:
            sys.exit(1)
        force_exit.add(1)
        logging.warning('Event loop is running... wait for a prompt '
                        'and type \'exit\' for a clean exit or '
                        'press CTRL+C again if you really want quit now.')
    else:
        sys.exit('You pressed CTRL+C, quit...')


if __name__ == '__main__':

    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-u',
        '--user',
        type=str,
        help='User for login. If user is not given it\'s asked from the tty.')

    parser.add_argument(
        '-p',
        '--password',
        type=str,
        help='Password to use when connecting to server. If password is '
        'not given it\'s asked from the tty.')

    parser.add_argument(
        '-d',
        '--dbname',
        type=str,
        help='Database name to connect to. If dbname is '
        'not given it\'s asked from the tty.')

    parser.add_argument(
        '-s',
        '--servers',
        type=str,
        default='localhost:9000',
        help='Server(s) to connect to. Multiple hosts can be provided and '
        'should be separated with comma\'s or spaces. '
        'Each host should be entered like: '
        '<hostname_or_ipv4_or_[ipv6]>:<port>')

    parser.add_argument(
        '-l', '--log-level',
        default='warning',
        help='set the log level',
        choices=['debug', 'info', 'warning', 'error', 'critical'])

    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='print version information and exit')

    args = parser.parse_args()

    if args.version:
        sys.exit('''
SiriDB Prompt {version}
Maintainer: {maintainer} <{email}>
Home-page: http://siridb.net
        '''.strip().format(version=__version__,
                           maintainer=__maintainer__,
                           email=__email__))

    logger = logging.getLogger()
    logger.setLevel(logging._nameToLevel[args.log_level.upper()])

    formatter = logging.Formatter(
        fmt='\033[93m[%(levelname)1.1s]\x1b[0m %(message)s',
        style='%')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    try:
        while not args.user:
            args.user = prompt('Username: ')

        while not args.password:
            args.password = prompt('Password: ', is_password=True)

        while not args.dbname:
            args.dbname = prompt('Database name: ')
    except KeyboardInterrupt:
        signal_handler()

    try:
        hostlist = get_hostlist(args.servers)
    except ValueError:
        sys.exit('Invalid servers, expecting something like: '
                 'server1.local:9000,[::1]:9000 ...')

    cluster = SiriDBClient(
        username=args.user,
        password=args.password,
        dbname=args.dbname,
        hostlist=hostlist,
        keepalive=True)

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(prompt_loop(cluster))
    except:
        pass

    sys.exit(0)
