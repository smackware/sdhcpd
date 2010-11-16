import shelve

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

    def isIpValidForNetmask(ip, netmask):
        for d in xrange(4, 0, -1):
            if ip[d-1] & netmask[d-1] != ip[d-1]:
                return False
        return True

    def leaseIpAddress(self, ip, requester_hwmac, lease_time):
        ip_str = '.'.join(map(str,ip))
        lease_expiry = time.time() + lease_time
        self.db[ip_str] = {
                    'hwmac': requester_hwmac,
                    'lease_expiry': lease_expiry
                }

    def allocateIpAddress(self, subnet, netmask, requester_hwmac):
        """
        subnet = [192,168,0,0]
        netmask = [255,255,0,0]
        """
        # This is not going to be the best algorithm of all... ^____^
        # TODO: Add cache per-subnet
        ip = list(subnet)
        for d in xrange(subnet[2], 255):
            ip[2] = d
            for i in xrange(1, 255):
                ip[3] = i
                if not self.isIpValidForNetmask(ip, netmask):
                    continue
                if self.isIpLeased(ip):
                    continue
        # We 'temporarly' lease the IP for, assuming the client ACKs it
        self.leaseIpAddress(ip, requester_hwmac, self.wait_ack_lease_time)
        return ip


