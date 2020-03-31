import struct
from ros_packer.ros_header_v1 import RosHeaderV1


class RosLzmaSubheader(RosHeaderV1):
    """Structure of the header of each payload file. Total 32 byte in little endian except time stamp year.
    SIZE can be found at 0x05 of the payload and describes the length of the uncompressed LZMA payload.

    0           1           2           3           4
    0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5  6
    | ARC_MAGIC | ARC_INDEX |     TIME STAMP        |
    -------------------------------------------------
    |  UNKNOWN1 |   SIZE    |      UNKNOWN2         |
    """

    HEADER_SIZE = 32
    ARC_MAGIC = struct.pack('4s', 'BL01'.encode('ascii'))  # 4 Bytes
    ARC_INDEX = struct.pack('4s', '2.00'.encode('ascii'))  # 4 Bytes
    UNKNOWN2 = struct.pack('<II', 0, 0)  # 8 Bytes

    def __init__(self, time_stamp_sec, time_stamp_min, time_stamp_hour, time_stamp_day, time_stamp_month,
                 time_stamp_year, size):

        self.time_stamp = struct.pack('<6B', time_stamp_sec, time_stamp_min, time_stamp_hour, self.UNKNOWN_TIME,
                                      time_stamp_day, time_stamp_month)
        self.time_stamp = self.time_stamp + struct.pack('>h', time_stamp_year)  # 8 Bytes time stamp, year in big-endian
        self.size = size  # 4 Byte size of uncompressed LZMA archive

    def set_time(self, time):
        self.time_stamp = time

    def get_bytes(self):
        return self.ARC_MAGIC + self.ARC_INDEX + self.time_stamp + self.UNKNOWN1 + self.size + self.UNKNOWN2
