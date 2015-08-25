#!/usr/bin/env python3

import argparse
import re
import socket
import bwdb
import os
import shutil
import sys
from datetime import datetime
from pypacker import ppcap
from pypacker.layer12 import ethernet

global ip_filter
global hosts

def parse_args():
    global db
    parser = argparse.ArgumentParser(description='Process tcpdump output, with date prepended, into database..')
    parser.add_argument('files', type=str, nargs='+',
                        help='files or directory to process')
    parser.add_argument('-d', '--database', type=str,
                        default='database.db',
                        help='database')

    return parser.parse_args()


def process_dir(dirname):
    log_msg('Processing directory '+dirname+'.')
    for (root, dirs, files) in os.walk(dirname):
        for filename in sorted(files):
            if re.match('^.*\\.pcap$', filename):
                process_pcap(os.path.join(root, filename))
    log_msg('Done with '+dirname+'.')


def process_pcap(pcap_file):
    global done_path, process_path

    if not os.path.isfile(pcap_file):
        log_msg('Unable to process '+pcap_file+'.')
        return

    bandwidth = {}
    log_msg('Processing pcap '+pcap_file+'..', newline=False)

    base_file = os.path.basename(pcap_file)
    proc_file = os.path.join(process_path, base_file)
    done_file = os.path.join(done_path, base_file)

    shutil.move(pcap_file, proc_file)

    pcap = ppcap.Reader(filename=proc_file)
    last_minute = -1

    for ts, buf in pcap:
        (day, hour, minute, second) = ts_to_date(ts)
        pkt = get_packet_info(buf)

        if not pkt:
            continue

        length = pkt['length']
        src_ip = pkt['ip_src']
        src_mac = pkt['mac_src']
        dst_ip = pkt['ip_dst']
        dst_mac = pkt['mac_dst']

        if last_minute >= 0 and last_minute != minute:
            add_data(bandwidth)
            bandwidth = {}

        if add_host(src_ip, src_mac) and add_host(dst_ip, dst_mac):
            length = int(length / 2)

        if add_host(src_ip, src_mac):
            add_entry(bandwidth, day, hour, minute, hosts[src_ip]['host_id'], length)
        if add_host(dst_ip, dst_mac):
            add_entry(bandwidth, day, hour, minute, hosts[dst_ip]['host_id'], length)

        last_minute = minute

    add_data(bandwidth)

    shutil.move(proc_file, done_file)

    log_msg('!', date=False)


def ts_to_date(ts):
    dt_stamp = datetime.fromtimestamp(ts/1000000000)
    day = dt_stamp.strftime('%Y-%m-%d')
    hour = int(dt_stamp.strftime('%H'))
    minute = int(dt_stamp.strftime('%M'))
    second = int(dt_stamp.strftime('%S'))
    return (day, hour, minute, second)


def get_packet_info(buf):
    try:
        info = {'mac_src': '', 'mac_dst': '',
                'ip_src': '', 'ip_dst': '',
                'sport': 0, 'dport': 0,
                'length': 0}

        eth = ethernet.Ethernet(buf)
        if hasattr(eth, 'src_s'):
            info['mac_src'] = eth.src_s
            info['mac_dst'] = eth.dst_s

        ip = eth.upper_layer
        if hasattr(ip, 'src_s'):
            info['ip_src'] = ip.src_s
            info['ip_dst'] = ip.dst_s

        if hasattr(ip, 'len'):
            info['length'] = ip.len
        elif hasattr(ip, 'dlen'):
            info['length'] = ip.dlen

        #tcp = ip.upper_layer
        #if hasattr(tcp, 'sport'):
        #    info['sport'] = tcp.sport
        #    info['dport'] = tcp.dport

        return info
    except:
        return {}



def add_entry(table_dict, day, hour, minute, host_id, length):
    if day not in table_dict:
        table_dict[day] = {}
    if hour not in table_dict[day]:
        table_dict[day][hour] = {}
    if minute not in table_dict[day][hour]:
        table_dict[day][hour][minute] = {}
    if host_id not in table_dict[day][hour][minute]:
        table_dict[day][hour][minute][host_id] = []
    table_dict[day][hour][minute][host_id].append(int(length))


def add_data(data):
    global db
    log_msg('o', newline=False, date=False)
    flattened = flatten_data(data)
    if flattened:
        db.add_bandwidth(flattened)
    log_msg('.', newline=False, date=False)


def flatten_data(data):
    new_data = []
    for day in data:
        for hour in data[day]:
            for minute in data[day][hour]:
                for host_id in data[day][hour][minute]:
                    count = len(data[day][hour][minute][host_id])
                    total = sum(data[day][hour][minute][host_id])
                    new_data.append((day, hour, minute, host_id, total, count))
    return new_data


def add_host(ip_addr, mac_addr):
    global ip_filter, hosts
    if re.search(ip_filter, ip_addr):
        if ip_addr not in hosts:
            name = get_name_by_addr(ip_addr)
            host_id = db.add_host(addr=ip_addr, name=name, mac=mac_addr)
            hosts[ip_addr] = db.get_host_objs(host_id=host_id)[0]
            hosts[ip_addr]['new_name'] = name

        elif 'new_name' not in hosts[ip_addr]:
            name = get_name_by_addr(ip_addr)
            if hosts[ip_addr]['name'] != name:
                db.update_host(host_id=hosts[ip_addr]['host_id'], name=name)
            hosts[ip_addr]['new_name'] = name

        return True
    return False


def get_name_by_addr(addr):
    name = ''
    try:
        host_by_addr = socket.gethostbyaddr(addr)
        name = host_by_addr[0]
    except socket.herror:
        pass
    return name


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


def init_globals():
    global done_path, process_path
    script_path = os.path.dirname(os.path.realpath(__file__))
    process_path = os.path.realpath(os.path.join(script_path, '..', 'process'))
    done_path = os.path.realpath(os.path.join(script_path, '..', 'done'))

    os.makedirs(process_path, exist_ok=True)
    os.makedirs(done_path, exist_ok=True)

if __name__ == "__main__":
    global db, hosts, ip_filter

    init_globals()

    ip_filter = '^192\.168\.'
    hosts = {}

    args = parse_args()

    log_msg('Initializing load...')
    db = bwdb.DB(db=args.database)
    for obj in db.get_host_objs():
        hosts[obj['addr']] = obj

    for filename in args.files:
        if os.path.isfile(filename):
            process_pcap(filename)
        elif os.path.isdir(filename):
            process_dir(filename)
        elif os.path.isdir(filename):
            log_msg('Can not process '+filename+'.')

