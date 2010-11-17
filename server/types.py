from IPy import IP as _IP

def intToIpv4List(i):
    ip_list = [0,0,0,0]
    for l in xrange(4):
        ip_list[3-l] = int(i & 255)
        i = i >> 8
    return ip_list

class IP(_IP):
    def list(self):
        if self.version() == 4:
            return intToIpv4List(self.int())
        raise NotImplementedError("Don't know how to convert non-ipv4 to list")

    @classmethod
    def from_list(cls, ip_list):
        ip_int = 0
        if len(ip_list) == 4:
            for i in xrange(4):
                ip_int = (ip_int << 8) + ip_list[i]
            return cls(ip_int)
        raise NotImplementedError("Don't know how to convert non-ipv4 to list")


class MAC(object): 
    data = None

    def __init__(self, value=0):
        if isinstance(value, int):
            self.data = value
        elif isinstance(value, str):
            data = 0
            for d in map(lambda i: int(i,16), value.split(':')):
                data = (data << 8) + d
            self.data = data
        elif isinstance(value, list):
            data = 0
            for d in value:
                data = (data << 8) + d
            self.data = data

    def list(self):
        mac_int = self.data
        mac_list = [0,0,0,0,0,0]
        for l in xrange(6):
            mac_list[5-l] = int(mac_int & 255)
            mac_int = mac_int >> 8
        return mac_list

    def __eq__(self, other):
        return bool(self.data == other.data)

    def str(self):
        return ':'.join(map(lambda x: "%02x" % x, self.list()))

    def __str__(self):
        return self.str()

    def __repr__(self):
        return "MAC('%s')" % (self.str(), )




