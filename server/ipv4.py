import time
import shelve
from collections import namedtuple

from server.types import IP, MAC

IPLease = namedtuple('IPLease', "ip mac expiry")

class LeaseError(Exception):
    pass

class IPLeaseManager(object):
    db = None
    lease_db_filepath = None
    wait_ack_lease_time = 60

    def __init__(self, lease_db_filepath):
        self.lease_db_filepath = lease_db_filepath
        self.db = shelve.open(lease_db_filepath)

    def _is_valid_lease(self, lease_key):
        if self.db.has_key(lease_key) and \
            self.db[lease_key].expiry > time.time():
                return True
        return False

    def get_lease(self, ip=None, mac=None):
        if ip and mac:
            raise ValueError("Cannot specify both ip and mac")
        lease_key = str(ip or mac)
        if self._is_valid_lease(lease_key):
            return self.db[lease_key]
        return None

    def is_leased_to(self, ip, mac):
        lease = self.get_lease(ip=ip)
        return bool(lease and MAC(lease.mac) == mac)

    def delete_lease(self, ip=None, mac=None):
        if ip and mac:
            raise ValueError("Cannot specify both ip and mac")
        lease_key = str(ip or mac)
        if self._is_valid_lease(lease_key):
            ip_key = self.db[lease_key].ip
            mac_key = self.db[lease_key].mac
            del self.db[ip_key]
            del self.db[mac_key]

    def lease_ip_address(self, ip, mac, lease_time):
        if self.get_lease(ip=ip) and not self.is_leased_to(ip, mac):
            raise LeaseError("IP %s is already leased, but not to %s" % (str(ip), str(mac), ))
        self.delete_lease(mac=mac) # Remove any previous lease of this mac addr
        lease_expiry = int(time.time() + lease_time)
        ip_lease = IPLease(str(ip), str(mac), lease_expiry)
        self.db[str(ip)] = ip_lease
        self.db[str(mac)] = ip_lease

    def _find_available_ip(self, ipv4_network, mac):
        existing_lease = self.get_lease(mac=mac)
        if existing_lease and IP(existing_lease.ip) in ipv4_network:
            print "Giving valid IP %s already leased to %s" % (existing_lease.ip, str(mac))
            return IP(existing_lease.ip)
        elif existing_lease:
                print "The ip already leased for this host is not in the specified network."
        for ip in ipv4_network:
            if self.get_lease(ip=ip):
                continue
            ip = IP(ip.int())
            if ip.list()[3] == 0: # Do not allocate IPs with .0 ends
                continue
            return ip
        raise LeaseError("No available leases")
        
    def allocate_ip_address(self, ipv4_network, mac, requested_ip=None):
        """
        ipv4_network = IPy.IP
        """
        if requested_ip:
            self.lease_ip_address(requested_ip, mac, self.wait_ack_lease_time)
            ip = requested_ip
        else:
            ip = self._find_available_ip(ipv4_network, mac)
            self.lease_ip_address(ip, mac, self.wait_ack_lease_time)
        return ip


