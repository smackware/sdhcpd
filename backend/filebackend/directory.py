import os
import shlex
from glob import glob

from server.types import MAC

from backend.base import AbstractBackend, BackendEntry, BackendError
from backend.base import SimpleReadOnlyConfig

class DirectoryBackend(AbstractBackend):
    hosts = None
    groups = None
    host_by_mac = None

    def __init__(self, *args, **kwargs):
        AbstractBackend.__init__(self, *args, **kwargs)
        self.hosts = dict()
        self.groups = dict()
        self.host_by_mac = dict()
        data_dir_path = self.options.get("data_dir", None)
        if not data_dir_path:
            raise BackendError("Need to specify 'data_dir' in configuration file.")
        self._load_data()

    def _load_data(self):
        data_dir_path = self.options["data_dir"]
        for full_path in glob(os.path.join(data_dir_path, "*")):
            no_ext_path, file_ext = os.path.splitext(full_path)
            name = os.path.basename(no_ext_path)
            if file_ext == '.host':
                print "Loading host: " + name
                host = SimpleReadOnlyConfig(full_path)
                if host.has_key("chaddr"):
                    self.hosts[name] = SimpleReadOnlyConfig(full_path)
                    self.host_by_mac[host['chaddr']] = name
                else:
                    print "Host has no mac addr specified: " + name
            elif file_ext == '.group':
                print "Loading group: " + name
                self.groups[name] = SimpleReadOnlyConfig(full_path)
            else:
                raise BackendError("Unknown file extension '%s' in data directory: %s" % (full_path, ))

    def query_entry(self, packet):
        mac_str = str(MAC(packet.GetHardwareAddress()))
        print "Querying " + mac_str
        host_name = self.host_by_mac.get(mac_str, None)
        if host_name:
            host_data = self.hosts[host_name]
        else:
            host_data = {'groups': 'default'} # Undefined MACs go to group 'default'
        host_group_names = shlex.split(host_data.pop("groups", ""))
        host_group_names.append("default")
        for group_name in host_group_names:
            print "Seeking group " + group_name
            if not self.groups.has_key(group_name):
                continue
            joined_data = dict(self.groups[group_name])
            # Set only options not set yet by previous groups or the host itself:
            joined_data.update(host_data)
            host_data = joined_data
        if not len(host_data):
            return None
        return BackendEntry(options=host_data)
