from pydhcplib.dhcp_packet import *
from pydhcplib.dhcp_network import DhcpServer as _DhcpServer
from server.types import IP, MAC, word

from helper.dhcp import parse_ip_or_str
from server.ipv4 import IPLeaseManager, LeaseError

class DhcpServer(_DhcpServer):

    def __init__(self, dhcp_server_options, backends):
        _DhcpServer.__init__(self,dhcp_server_options["listen_address"],
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

    def _set_packet_options(self, packet, options):
        for k, v in options.iteritems():
            if isinstance(v, str):
                v = parse_ip_or_str(v)
            packet.SetOption(k, v)

    def HandleDhcpDiscover(self, packet):
        print "GOT: DISCOVER"
        mac = MAC(packet.GetHardwareAddress())
        requested_ip = packet.GetOption('requested_ip_address')
        entry_options = self._calculate_entry_options(packet)
        ipv4_network = self._get_ipv4_network(entry_options)
        self._set_packet_options(packet, entry_options)
        try:
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
        lease_time = word(1000)
        if self.ip_lease_manager.is_leased_to(ip, mac):
            self.ip_lease_manager.lease_ip_address(ip, mac, lease_time)
        else:
            print "Client %s requested IP %s not leased to it." % (str(mac), str(ip),)
            client_old_lease = self.ip_lease_manager.get_lease(mac=mac)
            if client_old_lease:
                self.ip_lease_manager.delete_lease(mac)
                print "Released lease of %s from %s" % (client_old_lease.ip, str(mac))
            return
        packet.SetOption('ip_address_lease_time', lease_time.bytes())
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
        self.ip_lease_manager.delete_lease(mac=MAC(packet.GetNetworkAddress()))

    def HandleDhcpRelease(self, packet):
        self.ip_lease_manager.delete_lease(mac=MAC(packet.GetNetworkAddress()))

    def HandleDhcpInform(self, packet):
        print "GOT: INFORM"
        mac = MAC(packet.GetHardwareAddress())
        entry_options = self._calculate_entry_options(packet)
        ipv4_network = self._get_ipv4_network(entry_options)
        self._set_packet_options(packet, entry_options)
        client_lease = self.ip_lease_manager.get_lease(mac=mac)
        if not client_lease:
            # Maybe send DHCP Deny?
            return None
        packet.SetOption('yiaddr', IP(client_lease.ip).list())
        packet.TransformToDhcpAckPacket()
        dest_relay_or_gateway = None
        if sum(packet.GetOption('giaddr')):
            dest_relay_or_gateway = str(IP.from_list(packet.GetOption('giaddr')))
        else:
            dest_relay_or_gateway = "255.255.255.255"
        print "SEND: ACK"
        print packet.str()
        self.SendDhcpPacketTo(packet, dest_relay_or_gateway, 68)
        print packet.str()
