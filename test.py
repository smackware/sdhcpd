import re
import time
from subprocess import Popen, PIPE, STDOUT
from pydhcplib.dhcp_packet import *
from pydhcplib.dhcp_network import *
from server.types import IP, MAC

from backend.ldapbackend import LDAPBackend
from backend.dummy import DummyBackend
from server.dhcp import IPLeaseManager, LeaseError

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
        elif network:
            return IP(network)
        elif subnet_mask and network_prefix:
            return IP.from_list(network_prefix).make_net(IP.from_list(subnet_mask))
        raise Exception("Cannot determine network info for client. Missing prefix or subnet information")

    def _calculate_entry_options(self, packet):
        joined_offer_options = dict()
        for backend in self.backends:
            backend_entry = backend.query_entry(packet)
            if not backend_entry:
                continue
            joined_offer_options.update(backend_entry.options)
        return joined_offer_options

    def HandleDhcpDiscover(self, packet):
        print "GOT: DISCOVER"
        mac = MAC(packet.GetHardwareAddress())
        requested_ip = packet.GetOption('requested_ip_address')
        entry_options = self._calculate_entry_options(packet)
        ipv4_network = self._get_ipv4_network(entry_options)
        packet.SetMultipleOptions(entry_options)
        try:
            if not sum(packet.GetOption('yiaddr')):
                requested_ip_data = packet.GetOption('requested_ip_address')
                if sum(requested_ip_data):
                    ip = self.ip_lease_manager.allocate_ip_address( \
                            ipv4_network, mac, \
                            requested_ip=IP.from_list(requested_ip_data) \
                            )
                else:
                    ip = self.ip_lease_manager.allocate_ip_address(ipv4_network, mac)
            packet.SetOption('yiaddr', ip.list())
        except LeaseError as e:
            print str(e)
            return
        packet.TransformToDhcpOfferPacket()
        print "SEND: OFFER"
        print packet.str()
        self.SendDhcpPacketTo(packet, "255.255.255.255", 68)

    def HandleDhcpRequest(self, packet):
        print "GOT: REQUEST"
        mac = MAC(packet.GetHardwareAddress())
        ip = IP.from_list(packet.GetOption('request_ip_address') or packet.GetOption('yiaddr'))
        if self.ip_lease_manager.is_leased_to(ip, mac):
            self.ip_lease_manager.lease_ip_address(ip, mac, 10000)
        else:
            print "Client %s requested IP %s not leased to it." % (str(mac), str(ip),)
            return
        packet.SetOption('ip_address_lease_time', [0,0,255,255])
        packet.SetOption('yiaddr', ip.list())
        packet.TransformToDhcpAckPacket()
        dest_relay_or_gateway = None
        if sum(packet.GetOption('giaddr')):
            dest_relay_or_gateway = str(IP.from_list(packet.GetOption('giaddr')))
        else:
            dest_relay_or_gateway = "255.255.255.255"
        print "SEND: ACK"
        print packet.str()
        self.SendDhcpPacketTo(packet, dest_relay_or_gateway, 68)

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
