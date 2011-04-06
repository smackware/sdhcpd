from backend.base import BackendEntry, BackendError, AbstractBackend

class DummyBackend(AbstractBackend):
    def query_entry(self, packet):
        options = {
                #'yiaddr': parse_ip_or_str("10.0.0.20"),
                'network': "10.0.0.0/24",
                'host_name': "host101"
                }
        print options
        return BackendEntry(options)

