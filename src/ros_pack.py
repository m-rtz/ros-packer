#!/usr/bin/env python3

import pathlib
import argparse

from ros_packer.ros_packer import check_ros, pack_ros, write_ros


def check_arguments(arguments):
    """
    Checking arguments and returns False if: DIR_TO_PACK does not exists, is no directory, is empty, OUTPUT
    already exists, MIRROR already exists or is no file; VERSION and MIRROR is set or neither.
    """

    if arguments.verbosity:
        print(
            '\nChecking Arguments:\ngiven directory: {}\ngiven output {}\nmirror file: {}\nselected '
            'header version: {}'.format(
                arguments.DIR_TO_PACK, arguments.output, arguments.mirror, arguments.version))

    if not arguments.DIR_TO_PACK.exists():
        print('Error: {} does not exist!'.format(arguments.DIR_TO_PACK.name))
        return False

    if not arguments.DIR_TO_PACK.is_dir():
        print('Error: {} is not a directory!'.format(arguments.DIR_TO_PACK.name))
        return False

    if not list(arguments.DIR_TO_PACK.glob('*')):
        print('Error: {} is empty!'.format(arguments.DIR_TO_PACK.name))
        return False

    if arguments.output.exists():
        print('Error: {} already exists!'.format(arguments.output.name))
        return False

    if arguments.mirror is not None:
        if not arguments.mirror.exists():
            print('Error: {} does not exists!'.format(arguments.mirror))
            return False

        if not arguments.mirror.is_file():
            print('Error: {} is not a file!'.format(arguments.mirror))
            return False

    if arguments.mirror is None and arguments.version is None:
        print('Error: No header version and no mirror file!')
        return False

    return True


def setup_arguments():
    parser = argparse.ArgumentParser(description='A simple packer for the ros firmmware container format.')
    parser.add_argument('-v', '--verbosity', help='increase output verbosity', action='store_true')
    parser.add_argument('-o', '--output', type=pathlib.Path, default=pathlib.Path('container.ros'),
                        help='name your output')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-m', '--mirror', type=pathlib.Path,
                       help='ros-file to mirror. This will help determine the header version')
    group.add_argument('-V', '--version', type=int, choices=[1, 2], help='select header version 1 or header version 2')
    parser.add_argument('DIR_TO_PACK', type=pathlib.Path, help='location of the unpacked ros structure.')
    args = parser.parse_args()
    return args


def main():
    arguments = setup_arguments()

    if not check_arguments(arguments):
        return 1

    if arguments.mirror is not None:
        if not check_ros(arguments.mirror):
            return 3

    ros_structure = pack_ros(arguments.DIR_TO_PACK, arguments.mirror, arguments.verbosity, arguments.version)

    if not write_ros(arguments.output, arguments.verbosity, ros_structure):
        return 4

    return 0


if __name__ == '__main__':
    exit(main())
