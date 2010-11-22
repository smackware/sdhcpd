import re
import time

from server import DhcpServer


from subprocess import Popen, PIPE, STDOUT

from helper.dhcp import parse_ip_or_str
from backend.ldapbackend import LDAPBackend
from backend.dummy import DummyBackend
from backend.filebackend.directory import DirectoryBackend
from server.ipv4 import IPLeaseManager, LeaseError

netopt = {'client_listen_port':"68",
          'server_listen_port':"67",
          'listen_address':"0.0.0.0"}

############# HELPERS
def parse_backend_options(options_filepath):
    options = dict()
    options_file = file(options_filepath)
    for line in options_file.readlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        option_name, option_value = map(lambda x: x.strip(), line.split(":", 1))
        if options.has_key(option_name):
            options[option_name] += " " + option_value
        else:
            options[option_name] = option_value
    options_file.close()
    # TODO Use DEBUG option
    for option_name, option_value in options.iteritems():
        print "BACKEND CONFIG: %s = %s" % (option_name, option_value)
    return options


ldap_backend = LDAPBackend(parse_backend_options("ldap_backend.conf"))
dir_backend = DirectoryBackend({'data_dir': './data_dir'})
test_backend = DummyBackend()
dhcp_server = DhcpServer(netopt, [ldap_backend, dir_backend])

while True :
    dhcp_server.GetNextDhcpPacket()
