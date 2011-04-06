import shlex

from server.types import IPv4, AddressRange, ByteObject, AddressRangeCollection

OPTION_TYPE_IP = 0x01
OPTION_TYPE_MULTIPLE_IP = 0x02
OPTION_TYPE_MAC = 0x03
OPTION_TYPE_STRING = 0x04
OPTION_TYPE_INT = 0x05

dhcp_option_name_by_alias = {
        'address': 'yiaddr',
        'hostname': 'host_name',
        'dns': 'domain_name_server',
        'lease_time': 'ip_address_lease_time',
        }

dhcp_option_type_by_name = {
        'yiaddr': OPTION_TYPE_IP,
        'ciaddr': OPTION_TYPE_IP,
        'giaddr': OPTION_TYPE_IP,
        'subnet_mask': OPTION_TYPE_IP,
        'giaddr': OPTION_TYPE_MULTIPLE_IP,
        'host_name': OPTION_TYPE_STRING,
        'time_server': OPTION_TYPE_MULTIPLE_IP,
        'domain_name_server': OPTION_TYPE_MULTIPLE_IP,
        'domain_name': OPTION_TYPE_STRING,
        'tftp_server_name': OPTION_TYPE_STRING,
        'bootfile_name': OPTION_TYPE_STRING,
        'ip_address_lease_time': OPTION_TYPE_INT,
}

def parse_ipv4_range(range_str):
    # 1.2.3.4 - 5.6.7.8
    if range_str.count(".") == 6 and range_str.count("-") == 1:
        start_ip_str, end_ip_str = map(lambda s: s.strip(), range_str.split("-", 1))
        start_ip = IPv4.from_str(start_ip_str)
        end_ip = IPv4.from_str(end_ip_str)
        high_ip = IPv4(int(end_ip) - int(start_ip))
        return AddressRange(start_ip, high_ip)
    if range_str.count(".") == 3:
        start_ip = IPv4(0)
        high_ip = IPv4(0)
        range_str_list = range_str.split(".", 3)
        for i in xrange(len(range_str_list)):
            if not range_str_list[i].count("-"):
                start_ip[i] = high_ip[i] = int(range_str_list[i])
            else:
                start_no, end_no = range_str_list[i].split("-",1)
                start_ip[i], high_ip[i] = map(int, (start_no, end_no))
        return AddressRange(start_ip, high_ip)

def parse_ipv4_range_collection(ranges_str):
    range_collection = AddressRangeCollection()
    for range_str in shlex.split(ranges_str):
        range_collection.append(parse_ipv4_range(range_str))
    return range_collection

def parse_dhcp_option(option_name, _value):
    option_name = dhcp_option_name_by_alias.get(option_name, option_name)
    option_type = dhcp_option_type_by_name.get(option_name, OPTION_TYPE_STRING)
    if option_type == OPTION_TYPE_IP:
        value = list(IPv4.from_str(_value))
    elif option_type == OPTION_TYPE_MULTIPLE_IP:
        byte_list = list()
        for ip_str in shlex.split(_value):
            ipv4 = IPv4.from_str(ip_str)
            byte_list.extend(ipv4)
        value = byte_list
    elif option_type == OPTION_TYPE_MAC:
        value = list(MAC(_value))
    elif option_type == OPTION_TYPE_STRING:
        value = list(ByteObject.from_ascii(_value))
    elif option_type == OPTION_TYPE_INT:
        value = list(ByteObject(4, _value))
    else:
        raise Exception("UNKNOWN OPTION TYPE")
    return (option_name, value)
