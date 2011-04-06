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
                dict.__setitem__(self, option_name, self[option_name] + " " + option_value)
            else:
                dict.__setitem__(self, option_name, option_value)
        file_handle.close()

def load_backend(config_filepath):
    import os
    options = SimpleReadOnlyConfig(config_filepath)
    module_import_path = options['backend_module']
    mod = __import__(module_import_path, fromlist=['Backend'])
    return mod.Backend(options)

def load_backends(backend_config_dirpath):
    import os
    import glob
    return map(load_backend, glob.glob(os.path.join(backend_config_dirpath, "*.conf")))

class AbstractBackend(object):
    def __init__(self, backend_options=dict()):
        self.options = backend_options
        self.on_load()

    def close(self):
        self.on_close()

    def query_options(self, mac_addr, existing_options=dict()):
        """
        Calculates the attributes for the entry 

        Accepts:
            existing_options - the existing entry options given by the packet, or lower-priority backends
        Returns:
            dict() of new or modified options. No need to include the existing_options.
        """

        return self._query_entry(mac_addr, existing_options)

    def on_load(self):
        pass

    def on_close(self):
        pass

    def _query_entry(self, mac_addr, existing_options):
        raise NotImplementedError()


