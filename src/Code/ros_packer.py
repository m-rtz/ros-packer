#!/usr/bin/env python3

import pathlib
import argparse
import datetime
import struct
from ros_payload_header import ros_payload_header
from ros_lzma_subheader import ros_lzma_subheader
from ros_header_v1 import ros_header_v1
from ros_header_v2 import ros_header_v2


def check_input(args):
    """Checking arguments and returns False if: DIR_TO_PACK does not exists, is no directory, is empty, OUTPUT
    already exists, MIRROR already exists or is no file; VERSION and MIRROR is set or neither."""

    if args.verbosity:
        print(
            '\n\t***Start checking the Arguments***\ngiven directory: {}\ngiven output {}\nmirror file: {}\nselected '
            'header version: {}\n'.format(
                args.DIR_TO_PACK, args.output, args.mirror, args.version))

    if not args.DIR_TO_PACK.exists():
        print('Error: {} does not exist!'.format(args.DIR_TO_PACK.name))
        return False

    if not args.DIR_TO_PACK.is_dir():
        print('Error: {} is not a directory!'.format(args.DIR_TO_PACK.name))
        return False

    if not args.DIR_TO_PACK.match('*'):
        print('Error: {} is empty!'.format(args.DIR_TO_PACK.name))
        return False

    if args.output.exists():
        print('Error: {} already exists!'.format(args.output.name))
        return False

    if args.mirror is not None:
        if not args.mirror.exists():
            print('Error: {} does not exists!'.format(args.mirror))
            return False

        if not args.mirror.is_file():
            print('Error: {} is not a file!'.format(args.mirror))
            return False

    if args.mirror is None and args.version is None:
        print('Error: No Headerversion and no Mirror file!')
        return False

    return True


def check_ros(args):
    """Checks if a given file matches ROS-file characteristcs and returns False if not"""
    ros_binary = args.mirror.read_bytes()
    if not ros_binary[24:28] == ros_header_v1.SIGNATURE:
        print('{} does not have "PACK" at 0x18'.format(args.mirror.name))
        return False

    if not (ros_binary[4:8] == ros_header_v1.ARC_INDEX or ros_binary[4:8] == ros_header_v2.ARC_INDEX):
        print('does not have a valid version index')
        return False

    return True


def analize_ros(args, ros_binary):
    """Determines the Headerversion of a ROS-file and returns unknowns and timestamps."""

    if ros_binary[4:8] == ros_header_v1.ARC_INDEX:
        if args.verbosity:
            print('looks like Header version 1')
        is_version1 = True

    elif ros_binary[4:8] == ros_header_v2.ARC_INDEX:
        if args.verbosity:
            print('looks like Header Version 2')
        is_version1 = False
    else:
        print('does not have a valid version index')

    if args.verbosity:
        print('Start collecting data...')

    if is_version1:
        data = {'time': ros_binary[8:15], 'unknown1': ros_binary[28:32], 'unknown2': ros_binary[37:49]}

    else:
        data = {'unknown1': ros_binary[29:33], 'unknown2': ros_binary[36:40], 'time': ros_binary[40:48],
                'unknown3': ros_binary[56:64], 'version': ros_binary[64:80]}
    return is_version1, data


def analize_payloadheader(args, payloadheader):
    """Inserts unknowns in Payloadheader"""
    ros_binary = args.mirror.read_bytes()
    for i in range(0, 60):
        if ros_binary[i * 16: (i * 16) + 16] == payloadheader.get_name():
            if args.verbosity:
                print('Update unknowns in payload header')
            payloadheader.set_unknown(ros_binary[(i * 16) + 16 + 8: (i * 16) + 16 + 16])
    return payloadheader


def analize_lzma_subheader(args, name, tmp_header):
    """Inserts unknowns and timestamp in LZMA-Subheader."""
    binary = args.mirror.read_bytes()
    name_len = len(name.encode('ascii'))
    for i in range(0, 60):
        if binary[i * 16: (i * 16) + name_len] == name.encode('ascii'):
            offset = struct.unpack('<L', binary[i * 16 + 16:i * 16 + 16 + 4])[0]
            tmp_header.set_time(binary[offset + 8:offset + 16])
            tmp_header.set_unknown1(binary[offset + 16:offset + 20])
            tmp_header.set_unknown2(binary[offset + 24:offset + 32])

    return tmp_header


def pack_ros(args):
    """Packs the content in on one single ros-file"""

    stack = []
    dir_entries = sum(1 for x in args.DIR_TO_PACK.iterdir())
    current_offset = dir_entries * ros_payload_header.HEADER_SIZE
    payload_checksum = 0
    time = datetime.datetime.today()

    if args.verbosity:
        print('\n\t***Start packing the Directory***\n')

    if args.version is not None:
        if args.version == 1:
            current_offset = current_offset + ros_header_v1.HEADER_SIZE
        if args.version == 2:
            current_offset = current_offset + ros_header_v2.HEADER_SIZE

    if args.mirror is not None:
        if analize_ros(args, args.mirror.read_bytes())[0]:
            current_offset = current_offset + ros_header_v1.HEADER_SIZE
        if not analize_ros(args, args.mirror.read_bytes())[0]:
            current_offset = current_offset + ros_header_v2.HEADER_SIZE

    for i in args.DIR_TO_PACK.glob('*'):
        if args.verbosity:
            print('File: {}'.format(i.name))
        binary = i.read_bytes()

        # create LZMA Subheader if necessary
        if binary[0:2] == (93).to_bytes(2, byteorder='little'):  # check if LZMA-magic is there
            if args.verbosity:
                print('{} looks like a LZMA archive!\ncreate Subheader for it...'.format(i.name))
            tmp_lzma_subheader = ros_lzma_subheader(time.second, time.minute, time.hour, time.day, time.month,
                                                    time.year, binary[5:9])

            if args.mirror is not None:  # mirror if necessary
                if args.verbosity:
                    print('looking for subheader to mirror...')
                tmp_lzma_subheader = analize_lzma_subheader(args, i.name, tmp_lzma_subheader)

            binary = tmp_lzma_subheader.get_bytes() + binary

        if args.verbosity:
            print('Creating Payload Header...')

        tmp_payload_header = ros_payload_header(i, len(binary), current_offset)

        if args.mirror is not None:  # mirror if necessary
            tmp_payload_header = analize_payloadheader(args, tmp_payload_header)

        stack.insert(0, (tmp_payload_header, binary))
        current_offset = current_offset + len(stack[0][1])
        if args.verbosity:
            print('Calculating partial checksum...\n')
        payload_checksum = payload_checksum + sum(stack[0][0].get_bytes()) + sum(stack[0][1])
        print('current payload checksum: {}'.format(payload_checksum))

    if args.version is not None:
        if args.version == 1:
            if args.verbosity:
                print('Creating Header Version 1')
            header = ros_header_v1(time.second, time.minute, time.hour, time.day, time.month, time.year,
                                   dir_entries, current_offset - ros_header_v1.HEADER_SIZE, payload_checksum)

            stack.insert(0, header)

        else:
            if args.verbosity:
                print('Creating Header Version 2')
            header = ros_header_v2(current_offset + 32, dir_entries, time.second,
                                   time.minute, time.hour, time.day, time.month, time.year,
                                   current_offset - ros_header_v2.HEADER_SIZE, payload_checksum)
            header.calc_checksums()
            stack.insert(0, header)

    if args.mirror is not None:
        data = analize_ros(args, args.mirror.read_bytes())

        if data[0]:
            header = ros_header_v1(time.second, time.minute, time.hour, time.day, time.month, time.year,
                                   dir_entries, current_offset - ros_header_v1.HEADER_SIZE, payload_checksum)
            header.set_timestamp(data[1]['time'])
            header.set_unknown1(data[1]['unknown1'])
            header.set_unknown2(data[1]['unknown2'])
            stack.insert(0, header)

        else:
            header = ros_header_v2(current_offset + 32, dir_entries, time.second,
                                   time.minute, time.hour, time.day, time.month, time.year,
                                   current_offset - ros_header_v2.HEADER_SIZE, payload_checksum)
            header.set_timestamp(data[1]['time'])
            header.set_unknown1(data[1]['unknown1'])
            header.set_unknown2(data[1]['unknown2'])
            header.set_unknown3(data[1]['unknown3'])
            header.set_version(data[1]['version'])
            header.calc_checksums()
            stack.insert(0, header)

    return stack


def write_ros(args, stack):
    """Writes a given ROS-structure to one single file."""
    if args.verbosity:
        print('\n\t***Starting writing ros file***\n')

    file = open(args.output.name, 'xb')

    if args.verbosity:
        print('write Header')
    file.write(stack[0].get_bytes())

    if args.verbosity:
        print('write Payloadheader')
    for i in reversed(stack):
        if type(i) is tuple:
            file.write(i[0].get_bytes())

    if args.verbosity:
        print('write Payload data')
    for i in reversed(stack):
        if type(i) is tuple:
            file.write(i[1])

    file.close()

    return True


def main():
    parser = argparse.ArgumentParser(description='An (hopefully) simple and robust ros packer. Should be intuitive, '
                                                 'so just try throwing some directories at it.')
    parser.add_argument('-v', '--verbosity', help='increase output verbosity', action='store_true')
    parser.add_argument('-o', '--output', type=pathlib.Path, default=pathlib.Path('container.ros'),
                        help='name your output')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-m', '--mirror', type=pathlib.Path,
                       help='ROS-file to mirror. This will help determine the header version')
    group.add_argument('-V', '--version', type=int, choices=[1, 2], help='select header version 1 or header version 2')
    parser.add_argument('DIR_TO_PACK', type=pathlib.Path, help='location of the unpacked ros structure.')
    args = parser.parse_args()

    if not check_input(args):
        return 1

    if args.mirror is not None:
        if not check_ros(args):
            return 3

    ros_structure = pack_ros(args)

    if not write_ros(args, ros_structure):
        return 4

    return 0


if __name__ == '__main__':
    exit(main())
