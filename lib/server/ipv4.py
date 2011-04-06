import time
import shelve
from collections import namedtuple

from server.types import IPv4, MAC

IPLease = namedtuple('IPLease', "ip_str mac_str expiry_timestamp")

class LeaseError(Exception):
    pass

class IPLeaseManager(object):
    db = None
    lease_db_filepath = None
    wait_ack_lease_time = 60

    def __init__(self, lease_db_filepath):
        self.lease_db_filepath = lease_db_filepath
        self.db = shelve.open(lease_db_filepath)

    def _is_active_lease(self, _lease_key):
        """Check if a lease exists and active

        _lease_key - IP or MAC object

        """

        lease_key = str(_lease_key)
        try:
            self.db[lease_key].expiry_timestamp > time.time()
            return True
        except KeyError:
            return False


    def get_lease(self, ip=None, mac=None):
        if ip and mac:
            raise ValueError("Cannot specify both ip and mac")
        lease_key = str(ip or mac)
        if self._is_active_lease(lease_key):
            return self.db[lease_key]
        return None

    def was_last_leased_to(self, ip, mac):
        lease = self.db.get(str(ip), None)
        return bool(lease and lease.mac_str == str(mac))

    def is_currently_leased_to(self, ip, mac):
        return self._is_active_lease(ip) and self.was_last_leased_to(ip, mac)

    def delete_lease(self, ip=None, mac=None):
        if ip and mac:
            raise ValueError("Cannot specify both ip and mac")
        lease_key = str(ip or mac)
        if self.db.has_key(lease_key):
            ip_key = self.db[lease_key].ip_str
            mac_key = self.db[lease_key].mac_str
            try:
                del self.db[ip_key]
                del self.db[mac_key]
            except Exception as e:
                raise LeaseError(str(e))

    def _lease_ip_address(self, ip, mac, lease_time):
        # Delete any previous lease of ip and mac
        self.delete_lease(mac=mac) 
        self.delete_lease(ip=ip) 
        # Calculate expiry time
        lease_expiry = int(time.time() + lease_time)
        # Save the lease
        ip_lease = IPLease(str(ip), str(mac), lease_expiry)
        self.db[str(ip)] = ip_lease
        self.db[str(mac)] = ip_lease

    def lease_ip_address(self, ip, mac, lease_time):
        existing_ip_lease = self.get_lease(ip=ip)
        if existing_ip_lease and not self.was_last_leased_to(ip, mac):
            raise LeaseError("Cannot lease %s to %s, it's leased to %s" % \
                    (str(ip), str(mac), existing_lease.mac_str, ))
        return self._lease_ip_address(ip, mac, lease_time)

    def _find_available_ip(self, address_range_collection):
        for ip in address_range_collection:
            if self.get_lease(ip=ip):
                continue
            if ip[3] == 0: # Do not allocate IPs with .0 ends
                continue
            return ip
        raise LeaseError("No available leases")

    def reallocate_ip_address(self, mac, ip):
        self._lease_ip_address(ip, mac, self.wait_ack_lease_time)
        
    def allocate_ip_address(self, address_range_collection, mac, requested_ip=None, use_existing_if_able=True):
        """
        """
        ip = None
        old_lease_ip = None
        old_mac_lease = self.get_lease(mac=mac)
        if old_mac_lease:
            old_lease_ip = IPv4.from_str(old_mac_lease.ip_str)
        # If the host requested a specific IP and it is available and within the network range,
        # allow it
        if requested_ip and requested_ip in address_range_collection and \
                (not self._is_active_lease(requested_ip) or self.was_last_leased_to(requested_ip, mac)):
            ip = requested_ip
        # If this MAC had a lease, and the lease is allowed within the given range, give that ip
        elif use_existing_if_able and old_lease_ip and old_lease_ip in address_range_collection:
            ip = old_lease_ip
        # If all else fails, allocate a new IP
        else:
            ip = self._find_available_ip(address_range_collection,)
        # We temporarily lease the IP, so we're sure not to give it to anyone else
        self._lease_ip_address(ip, mac, self.wait_ack_lease_time)
        return ip
