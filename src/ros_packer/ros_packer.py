import datetime
import pathlib
import struct
from typing import List, Union, Tuple, Dict

from ros_packer.ros_header_v1 import RosHeaderV1
from ros_packer.ros_header_v2 import RosHeaderV2
from ros_packer.ros_lzma_subheader import RosLzmaSubheader
from ros_packer.ros_payload_header import RosPayloadHeader


def check_ros(mirror_file: pathlib.Path) -> bool:
    """
    Checks if a given file matches ROS-file characteristics and returns False if not
    """
    ros_binary = mirror_file.read_bytes()
    if not ros_binary[24:28] == RosHeaderV1.SIGNATURE:
        print('{} does not have "PACK" at 0x18, sure it is a ros file?'.format(mirror_file.name))
        return False

    if not (ros_binary[4:8] == RosHeaderV1.ARC_INDEX or ros_binary[4:8] == RosHeaderV2.ARC_INDEX):
        print('does not have a valid version index, sure it is a ros file?')
        return False

    return True


def analyze_ros(ros_binary: bytes) -> Tuple[bool, Dict[str, bytes]]:
    """
    Determines the header version of a ROS-file and returns unknowns and timestamps.
    """
    if ros_binary[4:8] == RosHeaderV1.ARC_INDEX:
        is_version1 = True

    elif ros_binary[4:8] == RosHeaderV2.ARC_INDEX:
        is_version1 = False
    else:
        raise ValueError('Container does not have a valid version index')

    if is_version1:
        data = {'time': ros_binary[8:15], 'unknown1': ros_binary[28:32], 'unknown2': ros_binary[37:49]}

    else:
        data = {'unknown1': ros_binary[28:32], 'unknown2': ros_binary[36:40], 'time': ros_binary[40:48],
                'unknown3': ros_binary[56:64], 'version': ros_binary[64:80]}

    return is_version1, data


def analyze_payload_header(mirror_file: pathlib.Path, verbose: bool, payloadheader: RosPayloadHeader) -> None:
    """
    Inserts unknowns in payload header
    """
    ros_binary = mirror_file.read_bytes()
    for i in range(0, 60):
        if ros_binary[i * 16: (i * 16) + 16] == payloadheader.get_name():
            if verbose:
                print('Update unknowns in payload header')
            payloadheader.set_unknown(ros_binary[(i * 16) + 16 + 8: (i * 16) + 16 + 16])


def analyze_lzma_subheader(mirror_file: pathlib.Path, name: str, tmp_header: RosLzmaSubheader) -> None:
    """Inserts unknowns and timestamp in LZMA-subheader."""

    binary = mirror_file.read_bytes()
    name_len = len(name.encode('ascii'))
    for i in range(0, 60):
        if binary[i * 16: (i * 16) + name_len] == name.encode('ascii'):
            offset = struct.unpack('<L', binary[i * 16 + 16:i * 16 + 16 + 4])[0]
            tmp_header.set_time(binary[offset + 8:offset + 16])
            tmp_header.set_unknown1(binary[offset + 16:offset + 20])
            tmp_header.set_unknown2(binary[offset + 24:offset + 32])


def init_packing(offset: int, version: int, mirror_file: pathlib.Path) -> int:
    """
    Adds the header length to a given offset.
    """

    if version is not None:
        if version == 1:
            offset = offset + RosHeaderV1.HEADER_SIZE
        if version == 2:
            offset = offset + RosHeaderV2.HEADER_SIZE

    if mirror_file and mirror_file.is_file():
        if analyze_ros(mirror_file.read_bytes())[0]:
            offset = offset + RosHeaderV1.HEADER_SIZE
        if not analyze_ros(mirror_file.read_bytes())[0]:
            offset = offset + RosHeaderV2.HEADER_SIZE

    return offset


def create_header(source_directory: pathlib.Path, mirror_file: pathlib.Path, verbose: bool, version: int, offset: int, payload_checksum: int) -> Union[RosHeaderV1, RosHeaderV2]:
    """
    Creates the header including mirroring, if selected.
    """
    dir_entries = sum(1 for x in source_directory.iterdir())
    time = datetime.datetime.today()

    if version is not None:
        if version == 1:
            if verbose:
                print('creating header version 1')
            header = RosHeaderV1(time.second, time.minute, time.hour, time.day, time.month, time.year,
                                 dir_entries, offset - RosHeaderV1.HEADER_SIZE, payload_checksum)

        else:
            if verbose:
                print('creating header version 2')
            header = RosHeaderV2(offset + 32, dir_entries, time.second,
                                 time.minute, time.hour, time.day, time.month, time.year,
                                 offset - RosHeaderV2.HEADER_SIZE, payload_checksum)
            header.calc_checksums()

    if mirror_file and mirror_file.is_file():
        data = analyze_ros(mirror_file.read_bytes())

        if data[0]:
            header = RosHeaderV1(time.second, time.minute, time.hour, time.day, time.month, time.year,
                                 dir_entries, offset - RosHeaderV1.HEADER_SIZE, payload_checksum)
            header.set_timestamp(data[1]['time'])
            header.set_unknown1(data[1]['unknown1'])
            header.set_unknown2(data[1]['unknown2'])

        else:
            header = RosHeaderV2(offset + 32, dir_entries, time.second,
                                 time.minute, time.hour, time.day, time.month, time.year,
                                 offset - RosHeaderV2.HEADER_SIZE, payload_checksum)
            header.set_timestamp(data[1]['time'])
            header.set_unknown1(data[1]['unknown1'])
            header.set_unknown2(data[1]['unknown2'])
            header.set_unknown3(data[1]['unknown3'])
            header.set_version(data[1]['version'])
            header.calc_checksums()

    return header


def pack_ros(source_directory: pathlib.Path, mirror_file: pathlib.Path, verbose: bool, version: int) -> List[Union[Union[RosPayloadHeader, RosHeaderV1], Tuple[Union[RosPayloadHeader, RosHeaderV1], bytes]]]:
    """
    Packs the content in on one single ros-file
    """
    stack = []
    dir_entries = sum(1 for x in source_directory.iterdir())
    current_offset = dir_entries * RosPayloadHeader.HEADER_SIZE
    payload_checksum = 0
    time = datetime.datetime.today()

    if verbose:
        print('\nStart packing:')

    current_offset = init_packing(current_offset, version, mirror_file)

    for i in source_directory.iterdir():
        if verbose:
            print('\nFile: {}'.format(i.name))
        binary = i.read_bytes()

        # create LZMA subheader if necessary
        if binary[0:2] == (93).to_bytes(2, byteorder='little'):  # check if LZMA-magic is there
            if verbose:
                print('{} looks like a LZMA archive! creating subheader'.format(i.name))
            tmp_lzma_subheader = RosLzmaSubheader(time.second, time.minute, time.hour, time.day, time.month,
                                                  time.year, binary[5:9])

            if mirror_file and mirror_file.is_file():  # mirror if necessary
                if verbose:
                    print('mirroring subheader')
                analyze_lzma_subheader(mirror_file, i.name, tmp_lzma_subheader)

            binary = tmp_lzma_subheader.get_bytes() + binary

        if verbose:
            print('creating payload header')

        tmp_payload_header = RosPayloadHeader(i, len(binary), current_offset)

        if mirror_file and mirror_file.is_file():  # mirror if necessary
            analyze_payload_header(mirror_file, verbose, tmp_payload_header)

        stack.insert(0, (tmp_payload_header, binary))
        current_offset = current_offset + len(stack[0][1])
        if verbose:
            print('calculating partial checksum')
        payload_checksum = payload_checksum + sum(stack[0][0].get_bytes()) + sum(stack[0][1])

    stack.insert(0, create_header(source_directory, mirror_file, verbose, version, current_offset, payload_checksum))

    return stack


def write_ros(output_path: pathlib.Path, verbose: bool, stack: List[Union[Union[RosPayloadHeader, RosHeaderV1], Tuple[Union[RosPayloadHeader, RosHeaderV1], bytes]]]) -> bool:
    """
    Writes a given ROS-structure to one single file.
    """
    if verbose:
        print('\nStart writing')

    file = open(output_path.name, 'xb')

    if verbose:
        print('write header')
    file.write(stack[0].get_bytes())

    if verbose:
        print('write payload header')
    for i in reversed(stack):
        if isinstance(i, tuple):
            file.write(i[0].get_bytes())

    if verbose:
        print('write payload data\ndone.')
    for i in reversed(stack):
        if isinstance(i, tuple):
            file.write(i[1])

    file.close()

    return True
