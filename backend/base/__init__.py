from collections import namedtuple

BackendEntry = namedtuple("BackendEntry", "options")

class BackendError(Exception):
    pass

class SimpleReadOnlyConfig(dict):
    def __setitem__(self, *args, **kwargs):
        raise NotImplementedError()

    def __init__(self, filepath):
        file_handle = file(filepath)
        for line in file_handle.readlines():
            line = line.strip()
            if not line or line.startswith("#"): # Skip comments
                continue
            option_name, option_value = map(lambda x: x.strip(), line.split(":", 1))
            if self.has_key(option_name):
                self[option_name] += " " + option_value
            else:
                self[option_name] = option_value
        file_handle.close()

def parse_backend_options(options_filepath):
    options = SimpleReadOnlyConfig(options_filepath)
    # TODO Use DEBUG option
    for option_name, option_value in options.iteritems():
        print "BACKEND CONFIG: %s = %s" % (option_name, option_value)
    return options

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
