import ldap
import ldapurl

from backend.base import BackendEntry, BackendError, AbstractBackend
from helper.dhcp import parse_ip_or_str

class LDAPBackend(AbstractBackend):
    ldap_conn = None
    ldap_uri = None
    ldap_to_dhcp_attribute_map = None
    ldap_object_class = None
    DEFAULT_LDAP_TO_DHCP_ATTRIBUTE_MAP = " \
            macaddress=chaddr \
            ipaddress=yiaddr \
            bootp_filename=file \
            next_server=siaddr \
            "

    def __init__(self, *args, **kwargs):
        AbstractBackend.__init__(self, *args, **kwargs)
        self.ldap_uri = ldapurl.LDAPUrl(self.options.get('ldap_uri', "ldap://localhost/"))
        self.__parse_ldap_to_dhcp_attribute_map()
        self.ldap_object_class = self.options.get("objectclass", "Device")


    def __parse_ldap_to_dhcp_attribute_map(self):
        """
        Parses the option string 'ldap_to_dhcp_attribute_map'
        Example value:  "macaddr=chaddr" "ipaddress=yiaddr"
        """
        import shlex
        self.ldap_to_dhcp_attribute_map = dict()
        options = shlex.split(self.options.get("ldap_to_dhcp_attribute_map", \
                self.DEFAULT_LDAP_TO_DHCP_ATTRIBUTE_MAP))
        for option in options:
            ldap_attr_name, dhcp_attr_name = option.split('=',1)
            self.ldap_to_dhcp_attribute_map[ldap_attr_name] = dhcp_attr_name

    def __connect(self):
        connect_string = "%s://%s" % (self.ldap_uri.urlscheme, self.ldap_uri.hostport)
        self.ldap_conn = ldap.initialize(connect_string)
        binddn = self.options.get("binddn", None)
        bindpw = self.options.get("bindpw", None)
        if binddn:
            result = self.ldap_backend.simple_bind_s(binddn, bindpw)

    def query_entry(self, packet):
        self.__connect()
        hwmac =  ':'.join(map(lambda x: "%02x" % x, packet.GetHardwareAddress()))
        ldap_filter = '(macaddress=%s)' % (hwmac)
        print "LDAP BACKED: searching " + ldap_filter
        attrs_to_get = self.ldap_to_dhcp_attribute_map.keys()
        try:
            results = self.ldap_conn.search_s(self.ldap_uri.dn, ldap.SCOPE_SUBTREE, ldap_filter, attrs_to_get)
        except ldap.SERVER_DOWN:
            raise BackendError("LDAP BACKEND cannot use backend")
        if not results:
            print "LDAP Backend: no results"
            return None # No configuration for this mac
        if len(results) > 1:
            raise BackendError("More than one offer results for: %s" % (package.GetHardwareAddress(),))
        offer_options = dict()
        for attr_name in attrs_to_get:
            dhcp_attr_name = self.ldap_to_dhcp_attribute_map[attr_name]
            value = results[0].get(attr_name, [])
            offer_options[dhcp_attr_name] = value
        return BackendEntry(offer_options)

    def close(self):
        self.ldap_conn.close()

