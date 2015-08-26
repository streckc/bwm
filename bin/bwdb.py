#!/usr/bin/env python3

import sqlite3
import re
from datetime import datetime

class DB:
    def __init__(self, test=False, db='database.db'):
        if test:
            self.conn = sqlite3.connect(':memory:')
        else:
            self.conn = sqlite3.connect(db)

        self.conn.isolation_level = None
        self.conn.text_factory = str
        self.db = db
        self.create_tables()


    def execute(self, command, arguments=[]):
        cursor = self.conn.cursor()

        if arguments and isinstance(arguments[0], (list, tuple)):
            cursor.executemany(command, arguments)
        else:
            cursor.execute(command, arguments)
        self.conn.commit()

        if command.split(' ')[0].lower() in ('insert', 'update'):
            return cursor.lastrowid
        else:
            return cursor.fetchall()


    def create_tables(self):
        self.execute('create table if not exists hosts ('
                     ' host_id integer primary key,'
                     ' addr text unique,'
                     ' name text,'
                     ' mac text'
                     ')')

        self.execute('create table if not exists bw_minute ('
                     ' day text,'
                     ' hour integer,'
                     ' minute integer,'
                     ' host_id integer,'
                     ' length integer,'
                     ' count integer'
                     ')')
        self.execute('create unique index if not exists bw_min_idx '
                     'on bw_minute ('
                     ' day, hour, minute, host_id, length, count'
                     ')')

        self.execute('create table if not exists bw_hour ('
                     ' day text,'
                     ' hour integer,'
                     ' host_id integer,'
                     ' length integer,'
                     ' count integer'
                     ')')
        self.execute('create unique index if not exists bw_hour_idx '
                     'on bw_hour ('
                     ' day, hour, host_id, length, count'
                     ')')

        self.execute('create table if not exists bw_day ('
                     ' day text,'
                     ' host_id integer,'
                     ' length integer,'
                     ' count integer'
                     ')')
        self.execute('create unique index if not exists bw_day_idx '
                     'on bw_day ('
                     ' day, host_id, length, count'
                     ')')


    def add_host(self, addr='', name='', mac=''):
        return self.execute('insert or ignore into hosts'
                            ' (addr, name, mac)'
                            ' values (?, ?, ?)',
                            (addr, name, mac))


    def update_host(self, host_id, addr=None, name=None, mac=None):
        sets = []
        arguments = []

        if addr is not None:
            sets.append('addr = ?')
            arguments.append(addr)
        if name is not None:
            sets.append('name = ?')
            arguments.append(name)
        if mac is not None:
            sets.append('mac = ?')
            arguments.append(mac)

        arguments.append(host_id)

        if len(arguments) > 1:
            self.execute('update hosts set '
                         ' '+', '.join(sets)+' '
                         ' where host_id = ?', arguments)


    def get_hosts(self, host_id=-1, addr='', name='', mac='', count=-1):
        command = 'select host_id, addr, name, mac from hosts'
        group_by = ''
        constraints = []
        arguments = []

        if int(host_id) >= 0:
            constraints.append('host_id = (?)')
            arguments.append(host_id)
        if addr:
            constraints.append('addr like (?)')
            arguments.append('%'+addr+'%')
        if name:
            constraints.append('name like (?)')
            arguments.append('%'+str(name)+'%')
        if mac:
            constraints.append('mac like (?)')
            arguments.append('%'+str(mac)+'%')
        if count >= 0:
            command = 'select hosts.host_id, hosts.addr, hosts.name, hosts.mac, max(bw_minute.count) as count from hosts join bw_minute using (host_id)'
            group_by = ' group by host_id'
            constraints.append('count > (?)')
            arguments.append(count)

        if len(constraints) > 0:
            return self.execute(command+' where '+' and '.join(constraints)+group_by, arguments)
        else:
            return self.execute(command+group_by)


    def get_host_objs(self, host_id=-1, addr='', name='', mac='', count=-1):
        hosts = []
        for row in self.get_hosts(host_id, addr, name, mac, count):
            hosts.append({'host_id':row[0],
                          'addr':row[1],
                          'name':row[2],
                          'mac':row[3]})
        return hosts


    def get_host_objs_by_bw(self, start='', end='', count=10):
        command = 'select hosts.host_id, hosts.addr, hosts.name, hosts.mac, sum(bw_minute.length) as length from hosts join bw_minute using (host_id)'
        group_by = ' group by host_id order by length desc'
        constraints = []
        arguments = []

        if start:
            (start_sql, start_args) = self.date_to_sql_constraint(start, '>=')
            if start_sql:
                constraints.append(start_sql)
                arguments.extend(start_args)
        if end:
            (end_sql, end_args) = self.date_to_sql_constraint(end, '<=')
            if end_sql:
                constraints.append(end_sql)
                arguments.extend(end_args)

        if len(constraints) > 0:
            hosts = self.execute(command+' where '+' and '.join(constraints)+group_by, arguments)
        else:
            hosts = self.execute(command+group_by)

        return hosts[0:count]


    def add_bandwidth(self, data):
        return self.execute('insert or ignore into bw_minute'
                            ' (day, hour, minute,'
                            '  host_id, length, count)'
                            ' values (?, ?, ?, ?, ?, ?)',
                            data)


    def get_bandwidth_objs(self, day='', hour=-1, minute=-1, host_id=-1, start='', end=''):
        bandwidth = []
        for row in self.get_bandwidth(day=day, hour=hour, minute=minute, host_id=host_id, start=start, end=end):
            bandwidth.append({'date': '%s %02d:%02d' % (row[0], row[1], row[2]),
                              'length': int(row[3]),
                              'count': int(row[4])})
        return bandwidth


    def get_bandwidth(self, resolution='minute', day='', hour=-1, minute=-1, host_id=-1, start='', end=''):
        command = 'select day, hour, minute, sum(length), sum(count) from bw_'+str(resolution)
        constraints = []
        arguments = []

        if day != '':
            constraints.append('day = (?)')
            arguments.append(day)
        if int(hour) >= 0:
            constraints.append('hour = (?)')
            arguments.append(hour)
        if int(minute) >= 0:
            constraints.append('minute = (?)')
            arguments.append(minute)
        if int(host_id) >= 0:
            constraints.append('host_id = (?)')
            arguments.append(host_id)

        if start:
            (start_sql, start_args) = self.date_to_sql_constraint(start, '>=')
            if start_sql:
                constraints.append(start_sql)
                arguments.extend(start_args)
        if end:
            (end_sql, end_args) = self.date_to_sql_constraint(end, '<=')
            if end_sql:
                constraints.append(end_sql)
                arguments.extend(end_args)

        if len(constraints) > 0:
            command += ' where '+' and '.join(constraints)

        command += ' group by day, hour, minute order by day, hour, minute'

        return self.execute(command, arguments)


    def get_record_count(self):
        command = 'select count(rowid) from bw_minute'
        return self.execute(command)[0][0]


    def date_to_sql_constraint(self, date_str='', oper='='):
        sql = ''
        args = []

        date_parts = re.findall('([0-9][0-9][0-9]?[0-9]?)[/-]([0-9][0-9]?)[/-]([0-9][0-9]?)', date_str)
        if date_parts:
            sql = 'day '+oper+' (?)'
            args.append('-'.join(date_parts[0]))

        return (sql, args)

