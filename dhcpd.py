import re
import sys
import time
import optparse

from server import DhcpServer


from subprocess import Popen, PIPE, STDOUT

from helper.dhcp import parse_ip_or_str
from backend import load_backends
from server.ipv4 import IPLeaseManager, LeaseError

BACKEND_CONFIG_DIRPATH = "backend.d"

netopt = {'client_listen_port':"68",
          'server_listen_port':"67",
          'listen_address':"0.0.0.0"}

def parse_argv():
    parser = optparse.OptionParser()
    parser.add_option("-n", "--no-fork", dest="no_fork", action="store_true",
                              help="Do not fork into a daemon")
    return parser.parse_args()

if __name__ == '__main__':
    (options, args) = parse_argv()
    print options
    print args
    sys.exit()

backends = load_backends(BACKEND_CONFIG_DIRPATH)
dhcp_server = DhcpServer("eth1", backends)

while True :
    dhcp_server.GetNextDhcpPacket()
