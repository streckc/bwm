#!/usr/bin/env python3

from datetime import datetime, date, timedelta
from utils import log_msg
from bwdb import DB
import argparse
import os
import sys


def init_hosts():
    global db
    hosts = {}
    for host in db.get_host_objs():
        hosts[host['addr']] = host
    return hosts


def init_globals(args):
    global app_root, db
    app_path = os.path.dirname(os.path.realpath(__file__))
    app_root = os.path.realpath(os.path.join(app_path, '..'))

    db = DB(db=args.database)


def parse_args():
    parser = argparse.ArgumentParser(description='Sniff interface to record metrics of IP packets.')

    #parser.add_argument('-c', '--config', type=str,
    #                    default='bwm.cfg',
    #                    help='configuration file')
    parser.add_argument('-d', '--database', type=str,
                        default='net_mon.db',
                        help='database')

    return parser.parse_args()


def rebuild_table(name=''):
    global db
    log_msg('rebuild_table: name='+str(name))


def archive_table(name='', day=''):
    global db
    log_msg('archive_table: name='+str(name)+', day='+str(day))


if __name__ == "__main__":
    global db

    log_msg('Initializing '+__file__+'...')

    args = parse_args()

    init_globals(args)

    rebuild_table('hour')
    rebuild_table('day')
    archive_table('minute', (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
    archive_table('hour', (date.today() - timedelta(weeks=26)).strftime('%Y-%m-%d'))
    archive_table('day', (date.today() - timedelta(weeks=520)).strftime('%Y-%m-%d'))

    log_msg('Done.')

