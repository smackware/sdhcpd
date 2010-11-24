import shlex

from IPy import IP as _IP


OPTION_TYPE_IP = 0x01
OPTION_TYPE_MULTIPLE_IP = 0x02
OPTION_TYPE_MAC = 0x03
OPTION_TYPE_STRING = 0x04


dhcp_option_name_by_alias = {
        'address': 'yiaddr',
        'hostname': 'host_name',
        }

dhcp_option_type_by_name = {
        'yiaddr': OPTION_TYPE_IP,
        'giaddr': OPTION_TYPE_MULTIPLE_IP,
        'host_name': OPTION_TYPE_STRING,
        'time_server': OPTION_TYPE_MULTIPLE_IP,
        'domain_name': OPTION_TYPE_STRING,
        'tftp_server_name': OPTION_TYPE_STRING,
        'bootfile_name': OPTION_TYPE_STRING,
}


def parse_dhcp_option(option_name, value):
    option_name = dhcp_option_name_by_alias.get(option_name, option_name)
    option_type = dhcp_option_type_by_name.get(option_name, OPTION_TYPE_STRING)
    if option_type == OPTION_TYPE_IP:
        value = IP(value).list()
    elif option_type == OPTION_TYPE_MULTIPLE_IP:
        byte_list = list()
        for ip_str in shlex.split(value):
            byte_list.extend(IP(ip_str).list())
        value = byte_list
    elif option_type == OPTION_TYPE_MAC:
        return MAC(value).list()
    elif option_type == OPTION_TYPE_STRING:
        byte_list = list()
        for l in value:
            byte_list.append(ord(l))
        value = byte_list
    else:
        raise Exception("UNKNOWN OPTION TYPE")
    return (option_name, value)

def word_to_byte_list(i):
    ip_list = [0,0,0,0]
    for l in xrange(4):
        ip_list[3-l] = int(i & 255)
        i = i >> 8
    return ip_list

class word(long):
    def bytes(self):
        return word_to_byte_list(self)

class IP(_IP):
    def list(self):
        if self.version() == 4:
            return word_to_byte_list(self.int())
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




