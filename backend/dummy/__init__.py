from backend.base import BackendEntry, BackendError, AbstractBackend
from helper.dhcp import parse_ip_or_str

class DummyBackend(AbstractBackend):
    def query_entry(self, packet):
        options = {
                #'yiaddr': parse_ip_or_str("10.0.0.20"),
                'subnet_mask': parse_ip_or_str("255.255.255.248"),
                'host_name': parse_ip_or_str("host101")
                }
        print options
        return BackendEntry(options)

