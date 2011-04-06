import re
from pydhcplib.type_strlist import strlist

IP_RE = re.compile("^\s*(\d+)\.(\d+)\.(\d+)\.(\d+)\s*$")
def parse_ip_or_str(value):
    m = IP_RE.match(value)
    if m:
        return list(map(int, m.groups()))
    return strlist(value).list()

