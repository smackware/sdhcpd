import time
import shelve

from IPy import IP
from pydhcplib.type_ipv4 import ipv4

class IPLeaseManager(object):
    db = None
    lease_db_filepath = None
    wait_ack_lease_time = 200

    def __init__(self, lease_db_filepath):
        self.lease_db_filepath = lease_db_filepath
        self.db = shelve.open(lease_db_filepath)

    def isIpLeased(self, ip):
        ip_str = '.'.join(map(str,ip))
        return self._leaseValid(ip_str)

    def _leaseValid(self, lease_key):
        if self.db.has_key(lease_key):
            print "LEASE EXISTS: " + lease_key
        if self.db.has_key(lease_key) and \
            self.db[lease_key]['lease_expiry'] > time.time():
                return True
        return False

    def getLeaseInfo(self, ip):
        ip_str = '.'.join(map(str,ip))
        print "IP: " + ip_str
        if self._leaseValid(ip_str):
            return self.db[ip_str]
        return None

    def getLeaseInfoByMac(self, hwmac):
        hwmac_str = ':'.join(map(lambda i: "%02x" % i, hwmac))
        if self._leaseValid(hwmac_str):
            return self.db[hwmac_str]
        return None

    def leaseIpAddress(self, ip, requester_hwmac, lease_time):
        ip_str = '.'.join(map(str,ip))
        hwmac_str = ':'.join(map(lambda i: "%02x" % i, requester_hwmac))
        lease_expiry = time.time() + lease_time
        self.db[ip_str] = {
                    'hwmac': hwmac_str,
                    'lease_expiry': lease_expiry
                }
        self.db[hwmac_str] = {
                    'ip': ip,
                    'lease_expiry': lease_expiry
                }

    def _find_available_ip(self, ipv4_network, requester_hwmac):
        current_lease = self.getLeaseInfoByMac(requester_hwmac)
        if current_lease and IP(ipv4(current_lease['ip']).str()) in ipv4_network:
            print "IP is already leased to this host."
            ip = current_lease['ip']
            return ip
        print "Trying to allocate new ip."
        for ip in ipv4_network:
            if self.isIpLeased(ip):
                continue
            if ip == ipv4_network.net():
                continue
            return ipv4(str(ip)).list()
        

    def allocateIpAddress(self, ipv4_network, requester_hwmac):
        """
        ipv4_network = IPy.IP
        """
        ip = self._find_available_ip(ipv4_network, requester_hwmac)
        if not ip:
            raise Exception("No available leases")
        self.leaseIpAddress(ip, requester_hwmac, self.wait_ack_lease_time)
        return ip


