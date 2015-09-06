#!/usr/bin/env python3

from datetime import datetime, date, timedelta
from utils import log_msg
from bwdb import DB
import argparse
import os
import sys


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
    parser.add_argument('-M', '--minute_table', type=int,
                        default=8,
                        help='weeks to keep minute table')
    parser.add_argument('-H', '--hour_table', type=int,
                        default=26,
                        help='weeks to keep hour table')
    parser.add_argument('-D', '--day_table', type=int,
                        default=520,
                        help='weeks to keep day table')

    return parser.parse_args()


def create_tables():
    global db
    log_msg('creating tables')
    db.create_tables()


def rebuild_table(name=''):
    global db
    log_msg('rebuilding table: name='+str(name))
    day = db.get_min_full_day()
    db.summarize_data(name, day, compare='>=')
    log_msg('rebuilding done')


def archive_table(name='', weeks=''):
    global db
    day = (date.today() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    log_msg('archiving table: name='+str(name)+', weeks='+str(weeks)+', day='+str(day))
    log_msg('archiving done')


if __name__ == "__main__":
    global db

    log_msg('Initializing '+__file__+'...')

    args = parse_args()

    init_globals(args)

    rebuild_table('hour')
    rebuild_table('day')
    archive_table('minute', args.minute_table)
    archive_table('hour', args.hour_table)
    archive_table('day', args.day_table)

    log_msg('Done.')

