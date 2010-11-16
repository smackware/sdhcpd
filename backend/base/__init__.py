from collections import namedtuple

BackendEntry = namedtuple("BackendEntry", "options subnet netmask")

class BackendError(Exception):
    pass

class AbstractBackend(object):
    def __init__(self, backend_options={}):
        self.options = backend_options

    def query_entry(self, packet):
        """
        This accepts a discover packet and returns a BackendEntry. Only the offer_packet is mandatory
        """
        return None

    def close(self):
        pass
