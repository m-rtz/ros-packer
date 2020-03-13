import struct


class ros_payload_header:
    """Structure of the header of each payload file. All little endian.

    0           1           2           3           4
    0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5  6
    |                   NAME                        |
    -------------------------------------------------
    | OFFSET    | LENGTH    |       UNKNOWN1        |
    -------------------------------------------------
    """

    HEADER_SIZE = 32
    UNKNOWN = struct.pack('<LL', 0, 0)  # 8 Byte

    def __init__(self, path, length, offset):
        self.name = struct.pack('16s', path.name.encode('ascii'))  # 16 Byte
        self.offset = struct.pack('<L', offset)  # 4 Byte
        self.length = struct.pack('<L', length)  # 4 Bytes

    def set_unknown(self, unknown):
        self.UNKNOWN = unknown

    def get_name(self):
        return self.name

    def get_bytes(self):
        # Check if 32 Byte
        return self.name + self.offset + self.length + self.UNKNOWN
