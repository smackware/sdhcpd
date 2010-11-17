import re
import time
from subprocess import Popen, PIPE, STDOUT
from pydhcplib.dhcp_packet import *
from pydhcplib.dhcp_network import *
from IPy import IP

from backend.ldapbackend import LDAPBackend
from backend.dummy import DummyBackend
from server.dhcp import IPLeaseManager

netopt = {'client_listen_port':"68",
          'server_listen_port':"67",
          'listen_address':"0.0.0.0"}

p = DhcpPacket()
p.SetOption('chaddr', [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
p.SetOption('hlen', [6])

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


class Server(DhcpServer):
    allow_requested_ips = True

    def __init__(self, dhcp_server_options, backends):
        DhcpServer.__init__(self,dhcp_server_options["listen_address"],
                            dhcp_server_options["client_listen_port"],
                            dhcp_server_options["server_listen_port"])
        self.backends = backends
        self.ip_lease_manager = IPLeaseManager("lease.db")

    def _get_ipv4_network(self, offer_options=dict()):
        """Returns an IPy.IP"""
        network = offer_options.pop("network", None)
        subnet_mask = offer_options.get("subnet_mask", None)
        network_prefix = offer_options.pop("network_prefix", None)
        if network and (subnet_mask or network_prefix):
            raise Exception("Cannot specify both network AND subnet_mask + network_prefix for an entry.")
        ip_network = None
        if network:
            ip_network = IP(network)
        elif subnet_mask and network_prefix:
            ip_network = IP('.'.join(map(str, network_prefix))).make_net('.'.join(map(str, subnet_mask)))
        else:
            raise Exception("Cannot determine network info for client. Missing prefix or subnet information")
        return ip_network

    def HandleDhcpDiscover(self, packet):
        print "Got discover!"
        joined_offer_options = dict()
        requested_ip = packet.GetOption('requested_ip_address')
        macaddr = packet.GetHardwareAddress()
        for backend in self.backends:
            backend_entry = backend.query_entry(packet)
            if not backend_entry:
                continue
            joined_offer_options.update(backend_entry.options)
        ipv4_network = self._get_ipv4_network(joined_offer_options)
        offer_packet = DhcpPacket()
        offer_packet.SetMultipleOptions(packet.GetMultipleOptions())
        offer_packet.SetMultipleOptions(joined_offer_options)
        offer_packet.TransformToDhcpOfferPacket()
        if not sum(offer_packet.GetOption('yiaddr')):
            if self.allow_requested_ips and sum(requested_ip):
                print "Client requested IP: " + str(requested_ip)
                if '.'.join(requested_ip) in ipv4_network: # Check that requested_ip is in the ipv4_network
                    current_lease = self.ip_lease_manager.getLeaseInfo(requested_ip)
                    if current_lease and current_lease['hwmac'] != macaddr:
                        raise Exception("Someone else is leasing that ip already")
                    offer_packet.SetOption('yiaddr', parse_ip_or_str(requested_ip))
                else:
                    print "ERROR Requested ip is not in the client's network. Not setting"
        if not sum(offer_packet.GetOption('yiaddr')):
                print "Allocating dynamic IP"
                network_prefix = map(int,str(ipv4_network.net()).split('.'))
                subnet_mask = map(int,str(ipv4_network.netmask()).split('.'))
                allocated_ip = self.ip_lease_manager.allocateIpAddress(network_prefix, subnet_mask, macaddr)
                offer_packet.SetOption('yiaddr', allocated_ip)
        print "Sending offer:"
        print offer_packet.str()
        self.SendDhcpPacketTo(offer_packet, "255.255.255.255", 68)

    def HandleDhcpRequest(self, packet):
        print "Got request:"
        print packet.str()
        self.ip_lease_manager.leaseIpAddress(packet.GetOption('yiaddr'))
        offer_packet = packet.TransformToAckDhcpPacket()
        print "Sending ACK:"
        self.SendDhcpPacketTo(offer_packet, "255.255.255.255", 68)

    def HandleDhcpDecline(self, packet):
        print packet.str()        

    def HandleDhcpRelease(self, packet):
        print packet.str()        

    def HandleDhcpInform(self, packet):
        print packet.str()

ldap_backend = LDAPBackend(parse_backend_options("ldap_backend.conf"))
test_backend = DummyBackend()
server = Server(netopt, [ldap_backend,test_backend])

while True :
    server.GetNextDhcpPacket()
