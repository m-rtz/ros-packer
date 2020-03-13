import struct


class ros_header_v1:
    """Header structure of a ros file. Total 32 Byte in little endian.

    0           1           2           3           4
    0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5  6
    | ARC_MAGIC | ARC_INDEX |     TIME STAMP        |
    -------------------------------------------------
    | LENGTH    |CHECKSUM   | SIGNATURE  |  UNKNOWN1|
    -------------------------------------------------
    |DIR_ENTRIES|               UNKNOWN 2           |
    -------------------------------------------------

    """
    HEADER_SIZE = 48
    SIGNATURE = struct.pack('4s', 'PACK'.encode('ascii'))  # 4 Bytes
    ARC_INDEX = struct.pack('4s', '1.01'.encode('ascii'))  # 4 Bytes
    ARC_MAGIC = struct.pack('4s', 'LS23'.encode('ascii'))  # 4 Bytes
    UNKNOWN1 = struct.pack('<I', 0)  # 4 Bytes
    UNKNOWN2 = struct.pack('<III', 0, 0, 0)  # 12 Bytes
    UNKNOWN_TIME = 0

    def __init__(self, time_stamp_sec, time_stamp_min, time_stamp_hour, time_stamp_day, time_stamp_month,
                 time_stamp_year, dir_entries, length, checksum):
        self.time_stamp = struct.pack('<6Bh', time_stamp_sec, time_stamp_min, time_stamp_hour, self.UNKNOWN_TIME,
                                      time_stamp_day, time_stamp_month, time_stamp_year)  # 8 Bytes
        self.dir_entries = struct.pack('<I', dir_entries)  # 4 Bytes
        self.length = struct.pack('<I', length)  # 4 Bytes without this header
        self.checksum = struct.pack('<I', checksum)  # 4 Bytes

    def set_timestamp(self, time):
        self.time_stamp = time
        return True

    def set_arc_magic(self, arc_magic):
        self.ARC_MAGIC = arc_magic

    def set_unknown1(self, unknown1):
        self.UNKNOWN1 = unknown1
        return True

    def set_unknown2(self, unknown2):
        self.UNKNOWN2 = unknown2
        return True

    def get_bytes(self):
        # Check if 48 Byte
        header = self.ARC_MAGIC + self.ARC_INDEX + self.time_stamp + self.length + self.checksum + self.SIGNATURE + self.UNKNOWN1 + self.dir_entries + self.UNKNOWN2
        return header
