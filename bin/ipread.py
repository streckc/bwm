# Tweaked from from https://askldjd.wordpress.com/2014/01/15/a-reasonably-fast-python-ip-sniffer/
# to remove any outgoing logic.  Sniffer meant to run on a monitor interface only.b

import socket, struct, os, array
from scapy.all import ETH_P_ALL
from scapy.all import select
from scapy.all import MTU
 
class IPSniff:
 
    def __init__(self, interface_name, on_ip_incoming):
 
        self.interface_name = interface_name
        self.on_ip_incoming = on_ip_incoming
 
        # The raw in (listen) socket is a L2 raw socket that listens
        # for all packets going through a specific interface.
        self.ins = socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
        self.ins.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2**30)
        self.ins.bind((self.interface_name, ETH_P_ALL))
 
    def __process_ipframe(self, pkt_type, eth_header, ip_header):
 
        eth_src = ':'.join('{:02x}'.format(c) for c in eth_header[0])
        eth_dst = ':'.join('{:02x}'.format(c) for c in eth_header[1])

        # Extract the 20 bytes IP header, ignoring the IP options
        fields = struct.unpack("!BBHHHBBHII", ip_header)
 
        ip_len = fields[2]
        ip_src = socket.inet_ntoa(ip_header[12:16])
        ip_dst = socket.inet_ntoa(ip_header[16:20])
 
        if not pkt_type == socket.PACKET_OUTGOING:
            if self.on_ip_incoming is not None:
                self.on_ip_incoming(eth_src, eth_dst, ip_src, ip_dst, ip_len)
 
    def recv(self):
        while True:
 
            pkt, sa_ll = self.ins.recvfrom(MTU)
 
            if type == socket.PACKET_OUTGOING:
                continue
 
            if len(pkt) <= 0:
                break
 
            eth_header = struct.unpack("!6s6sH", pkt[0:14])
 
            if eth_header[2] != 0x800 :
                continue
 
            ip_header = pkt[14:34]
 
            self.__process_ipframe(sa_ll[2], eth_header, ip_header)
 
#Example code to use IPSniff
def test_incoming_callback(src, dst, frame):
    #pass
    print("incoming - src=%s, dst=%s, frame len = %d"
        %(socket.inet_ntoa(src), socket.inet_ntoa(dst), len(frame)))
 
if __name__ == "__main__":
    ip_sniff = IPSniff('eth1', test_incoming_callback)
    ip_sniff.recv()
