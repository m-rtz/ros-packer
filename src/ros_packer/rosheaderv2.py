import struct
from ros_packer.rosheaderv1 import RosHeaderV1


class RosHeaderV2(RosHeaderV1):
    """
    Header structure of a ros file in version 2. Total 80 Byte in little endian.
    LENGTH describes the length of the ros container
    HEADER CHECKSUM is FFFFFFFF - byte sum.
    LENGTH1 is the length of the ros container without this header and CHECKSUM1 the byte sum of this scope.
    PAYLOAD_LENGTH is the length of the payloads including LZMA-Subheaders and PAYLOAD_CHECKSUM the byte sum of this scope

    0           1           2           3           4           5           6           7
    0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5  6  7  8  9  0  1
    ----------------------------------------------------------------------------------------------
    | ARC_MAGIC | ARC_INDEX |HEADER LEN |HEADER CHEC|  LENGTH 1 |CHECKSUM 1 | SIGNATURE |UNKNOWN1|
    ----------------------------------------------------------------------------------------------
    |DIR_ENTRIES| UNKNOWN 2 |     TIME STAMP        |PAYLO LENG |PAYLO CHECK|    UNKNOWN 3       |
    ----------------------------------------------------------------------------------------------
    |FIRMWARE VERSION                               |
    ------------------------------------------------
    """

    HEADER_SIZE = 80
    ARC_INDEX = struct.pack('4s', '2.00'.encode('ascii'))
    ARC_MAGIC = struct.pack('4s', 'BL01'.encode('ascii'))  # 4 Bytes
    HEADER_LENGTH = struct.pack('<I', HEADER_SIZE)
    HEADER_CHECKSUM = struct.pack('<I', 0)  # 4 Bytes
    UNKNOWN2 = struct.pack('<I', 0)  # 4 Bytes
    UNKNOWN3 = struct.pack('<II', 0, 0)  # 8 Bytes
    FIRMWARE_VERSION = struct.pack('16s', 'Firmware'.encode('ascii'))  # 16 Bytes

    def __init__(self, length1, dir_entries, time_stamp_sec, time_stamp_min, time_stamp_hour, time_stamp_day,
                 time_stamp_month, time_stamp_year, length2, payload_checksum2):
        self.header_checksum = struct.pack('<I', 0)  # 4 Bytes
        self.length1 = struct.pack('<I', length1)  # 4 Bytes
        self.payload_checksum1 = struct.pack('<I', 0)  # 4 Bytes
        self.dir_entries = struct.pack('<I', dir_entries)  # 4 Bytes
        self.time_stamp = struct.pack('<6Bh', time_stamp_sec, time_stamp_min, time_stamp_hour, self.UNKNOWN_TIME,
                                      time_stamp_day, time_stamp_month, time_stamp_year)  # 8 Bytes
        self.length2 = struct.pack('<I', length2)  # 4 Bytes
        self.payload_checksum2 = struct.pack('<I', payload_checksum2)  # 4 Bytes

    def calc_checksums(self):
        self.header_checksum = struct.pack('<I', 0)
        self.payload_checksum1 = struct.pack('<I', 0)
        self.payload_checksum1 = struct.pack('<I', sum(self.get_bytes()))  # 4 Bytes
        # 4 Bytes (0xFFFFFFFF - Checksum over this header)
        self.header_checksum = struct.pack('<I', 4294967295 - sum(self.get_bytes()))

    def set_unknown3(self, unknown3):
        self.UNKNOWN3 = unknown3
        return True

    def set_version(self, version):
        self.FIRMWARE_VERSION = version
        return True

    def get_bytes(self):
        header = self.ARC_MAGIC + self.ARC_INDEX + self.HEADER_LENGTH + self.header_checksum + self.length1 + \
                 self.payload_checksum1 + self.SIGNATURE + self.UNKNOWN1 + self.dir_entries + self.UNKNOWN2 + \
                 self.time_stamp + self.length2 + self.payload_checksum2 + self.UNKNOWN3 + self.FIRMWARE_VERSION
        return header
