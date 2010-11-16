import time
import shelve

from pydhcplib.type_ipv4 import ipv4

class IPLeaseManager(object):
    db = None
    lease_db_filepath = None
    wait_ack_lease_time = 10

    def __init__(self, lease_db_filepath):
        self.lease_db_filepath = lease_db_filepath
        self.db = shelve.open(lease_db_filepath)

    def isIpLeased(self, ip):
        ip_str = '.'.join(map(str,ip))
        if self.db.has_key(ip_str) and \
                self.db[ip_str]['lease_expiry'] > time.time(): # lease has yet to expire
            return True
        return False

    def getLeaseInfo(self, ip):
        ip_str = '.'.join(map(str,ip))
        return self.db.get(ip, None)

    def leaseIpAddress(self, ip, requester_hwmac, lease_time):
        ip_str = '.'.join(map(str,ip))
        lease_expiry = time.time() + lease_time
        self.db[ip_str] = {
                    'hwmac': requester_hwmac,
                    'lease_expiry': lease_expiry
                }

    def allocateIpAddress(self, network_prefix, netmask, requester_hwmac):
        """
        network_prefix = [192,168,0,0]
        netmask = [255,255,0,0]
        """

        ipv4_network_prefix = ipv4(network_prefix)
        ipv4_host_part_max = ipv4(map(lambda i: 255 ^ netmask[i], range(0,4)))
        print ipv4_host_part_max
        for i in xrange(1, ipv4_host_part_max.int()):
            ip = ipv4(ipv4_network_prefix.int() + i).list()
            if self.isIpLeased(ip):
                continue
            # We 'temporarly' lease the IP for, assuming the client ACKs it
            self.leaseIpAddress(ip, requester_hwmac, self.wait_ack_lease_time)
            return ip
        raise Exception("No available leases")


