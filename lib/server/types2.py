class ByteObject(object):
    _size = None
    _value = None

    def __init__(self, size, value=0):
        self._size = size
        self._set(value)

    def _set(self, _value):
        value = int(_value)
        if value < 0:
            raise ValueError()
        self._value = value

    def __setitem__(self, _key, _value):
        key = int(_key)
        value = int(_value)
        if key < 0 or key >= len(self):
            raise IndexError()
        if value < 0 or value > 255:
            raise ValueError()
        or_mask = value << (8*(len(self)-key-1))
        and_mask = 0
        for i in xrange(len(self)):
            and_mask = and_mask << 8
            if i != key:
                and_mask += 255
        self._value = (self._value & and_mask) | or_mask

    def __getitem__(self, _key):
        key = int(_key)
        if key < 0 or key >= len(self):
            raise IndexError()
        return int((self._value >> 8*(len(self) - key - 1)) & 255)

    def __len__(self):
        return self._size

    def __int__(self):
        return int(self._value)

    def __str__(self):
        return ''.join(map(chr, list(self)))

    @classmethod
    def from_ascii(cls, ascii_str):
        return cls.from_list(map(ord, ascii_str))

    @classmethod
    def from_list(cls, byte_list):
        if not isinstance(byte_list, list):
            raise TypeError()
        self = cls(len(byte_list))
        for i in xrange(len(byte_list)):
            self[i] = byte_list[i]
        return self

class IPv4(ByteObject):

    def __init__(self, _value=0):
        value = int(_value)
        ByteObject.__init__(self, 4, value)
    
    @classmethod
    def from_str(cls, ip_str):
        return cls.from_list(map(int, ip_str.split('.',3)))

    def __str__(self):
        return '.'.join(map(str,list(self)))


class IPv6(ByteObject):
    def __init__(self, _value=0):
        value = int(_value)
        ByteObject.__init__(self, 16, value)

    @classmethod
    def from_str(cls, ip_str):
        str_data = ip_str.split(':')
        int_data = list()
        self = cls()
        for value in str_data:
            if value:
                int_value = int(value, 16)
                int_data += [int_value >> 8, int_value & 255]
            else:
                int_data += [0] * (len(self) + 2 - len(str_data) * 2)
        return cls.from_list(int_data)

    @classmethod
    def from_ipv4(self, ipv4):
        ipv4_mark = ((255 << 8) + 255 ) << 32
        return IPv6(ipv4_mark + int(ipv4))

    def short_str(self):
        hex_list = list()
        compress_zero_count = 0
        compress_first_zero_index = -1
        current_zero_count = 0
        current_zero_index = None
        for i in xrange(0, len(self), 2):
            n1, n2 = self[i], self[i+1]
            if n1 + n2:
                hex_list.append("%x" % ((n1 << 8) + n2))
                current_zero_index = None
                current_zero_count = 0
            else:
                if current_zero_index is not None:
                    current_zero_count += 1
                else:
                    current_zero_index = i
                if current_zero_count > compress_zero_count:
                    compress_zero_count = current_zero_count
                    compress_first_zero_index = current_zero_index
                hex_list.append("0")
        if compress_first_zero_index == 0:
            hex_list[0:compress_zero_count + 1] = [':']
        elif compress_zero_count + compress_first_zero_index/2  + 1 == len(self)/2:
            hex_list[compress_first_zero_index/2:] = [':']
        elif compress_first_zero_index:
            hex_list[compress_first_zero_index/2:compress_first_zero_index/2 + compress_zero_count + 1] = ['']
        hex_str = ':'.join(hex_list)
        return hex_str

    def long_str(self):
        hex_list = list()
        for i in xrange(0, len(self), 2):
            n1, n2 = self[i], self[i+1]
            hex_list.append("%04x" % ((n1 << 8) + n2))
        return ':'.join(hex_list)

    def __str__(self):
        return self.short_str()
