#!/usr/bin/env python3

from ipread import IPSniff
from datetime import datetime
import bwdb
import argparse
import os
import socket
import sys



def log_msg(msg, dev='con', newline=True, date=True):
    if newline:
        msg += '\n'

    if date:
        date = str(datetime.strftime(datetime.now(), "%Y/%m/%d %H:%M:%S"))
        msg = date+': '+msg

    if dev == 'con':
        sys.stdout.write(msg)
        sys.stdout.flush()
    else:
        with open(dev,'a') as log_out:
            log_out.write(msg)


def add_host(ip_addr, mac_addr):
    global db, hosts
    name = get_name_by_addr(ip_addr)
    host_id = db.add_host(addr=ip_addr, name=name, mac=mac_addr)
    hosts[ip_addr] = {'host_id': host_id, 'addr': ip_addr, 'mac': mac_addr}
    log_msg('added host: host_id='+str(host_id)+', ip='+str(ip_addr)+', mac='+str(mac_addr)+', name='+name)


def get_name_by_addr(addr):
    name = ''
    try:
        host_by_addr = socket.gethostbyaddr(addr)
        name = host_by_addr[0]
    except socket.herror:
        pass
    return name


def add_to_data(host_id, length):
    global data

    minute_stamp = str(datetime.strftime(datetime.now(), '%Y-%m-%d|%H|%M'))

    if not data['timestamp'] == minute_stamp:
        insert_data_into_db(data['timestamp'], data['hosts'])
        data = {'timestamp': minute_stamp, 'hosts': {}}

    if host_id not in data['hosts']:
        data['hosts'][host_id] = {'count': 1, 'length': length}
    else:
        data['hosts'][host_id]['count'] += 1
        data['hosts'][host_id]['length'] += length


def insert_data_into_db(timestamp, metrics):
    global db

    if not timestamp:
        return

    new_data = []
    hosts = 0
    length = 0
    count = 0
    (day, hour, minute) = timestamp.split('|')
    for host_id in metrics:
        new_data.append((day, hour, minute, host_id, metrics[host_id]['length'], metrics[host_id]['count']))
        hosts += 1
        count += metrics[host_id]['count']
        length += metrics[host_id]['length']
    log_msg('adding: day='+str(day)+' '+str(hour)+':'+str(minute)+', hosts='+str(hosts)+', count='+str(count)+', length='+str(length))

    db.add_bandwidth(new_data)

def process_packet(eth_src, eth_dst, ip_src, ip_dst, ip_len):
    global ip_filter, hosts

    if ip_filter in ip_src:
        if ip_src not in hosts:
            add_host(ip_src, eth_src)
        add_to_data(hosts[ip_src]['host_id'], ip_len)
        ip_len = 0

    if ip_filter in ip_dst:
        if ip_dst not in hosts:
            add_host(ip_dst, eth_dst)
        add_to_data(hosts[ip_dst]['host_id'], ip_len)


def init_hosts():
    global db
    hosts = {}
    for host in db.get_host_objs():
        hosts[host['addr']] = host
    return hosts


def init_globals(args):
    global app_root, data, ip_filter, hosts, db
    app_path = os.path.dirname(os.path.realpath(__file__))
    app_root = os.path.realpath(os.path.join(app_path, '..'))

    ip_filter = args.filter
    data = {'timestamp': '', 'hosts': {}}
    db = bwdb.DB(db=args.database)
    hosts = init_hosts()



def parse_args():
    parser = argparse.ArgumentParser(description='Sniff interface to record metrics of IP packets.')

    #parser.add_argument('-c', '--config', type=str,
    #                    default='bwm.cfg',
    #                    help='configuration file')
    parser.add_argument('-d', '--database', type=str,
                        default='net_mon.db',
                        help='database')
    parser.add_argument('-f', '--filter', type=str,
                        default='192.168.1',
                        help='ip address filter')
    parser.add_argument('-i', '--interface', type=str,
                        default='eth1',
                        help='interface to sniff')

    return parser.parse_args()


if __name__ == "__main__":
    global data, db, hosts

    log_msg('Initializing...')

    args = parse_args()

    init_globals(args)

    ip_sniff = IPSniff(args.interface, process_packet)

    log_msg('Monitoring '+str(args.interface)+'...')
    try:
        ip_sniff.recv()
    except:
        insert_data_into_db(data['timestamp'], data['hosts'])
        ip_sniff.remove_promisc()

    log_msg('Done.')

