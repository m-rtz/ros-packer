from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from hashlib import sha3_512

import pytest

from ros_packer.ros_packer import check_ros

ROS_PACK = [str(Path(__file__).parent.parent / 'ros_pack.py'), ]
THIS_FILE = '{}'.format(Path(__file__).absolute())


@pytest.mark.parametrize('arguments, return_value', [
    ([], 2),                                                        # No DIR_TO_PACK given
    (['No_dir', ], 1),                                              # DIR_TO_PACK does not exists
    ([THIS_FILE, ], 1),                                             # DIR_TO_PACK is a file
    (['firmware/Test_container'], 1),                               # No mirror, no version, but DIR_TO_PACK
    (['-m', 'no_mirror', 'firmware/Test_container'], 1),            # Mirror does not exists
    (['-m', 'firmware', 'firmware/Test_container'], 1),             # Mirror is a Directory
    (['-V', '1', '-o', THIS_FILE, 'firmware/Test_container'], 1),   # Output already exists
])
def test_check_input(arguments, return_value):
    assert subprocess.call(ROS_PACK + list(arguments)) == return_value


def test_check_input_empty_directory():
    with TemporaryDirectory() as temp_dir:
        assert subprocess.call(ROS_PACK + ['-V', '1', temp_dir]) == 1


def test_ros_structure():
    assert not check_ros(mirror_file=Path(__file__).parent.parent / 'ros_packer/ros_packer.py')
    assert check_ros(mirror_file=Path(__file__).parent / 'firmware/test_container.ros')

def test_output():
    assert subprocess.call(ROS_PACK + ['-m', 'test/firmware/test_container.ros', '-o', 'tmp_container.ros',  'test/firmware/Test_container']) == 0
    assert sha3_512(open("test/firmware/test_container.ros", "rb").read()).hexdigest() == sha3_512(open("tmp_container.ros", "rb").read()).hexdigest()

