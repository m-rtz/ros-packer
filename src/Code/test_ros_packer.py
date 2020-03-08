import unittest
import subprocess


class TestInputParameters(unittest.TestCase):
    def test_inputs(self):

        # Test none input
        return_val = subprocess.call(['python', 'ros_packer.py'])
        self.assertEqual(return_val, 2)

        # Test DIR_TO_PACK does not exists
        return_val = subprocess.call(['python', 'ros_packer.py', 'No_dir'])
        self.assertEqual(return_val, 1)

        # Test DIR_TO_PACK is a file
        return_val = subprocess.call(['python', 'ros_packer.py', 'ros_packer.py'])
        self.assertEqual(return_val, 1)

        # Test DIR_TO_PACK is empty
        return_val = subprocess.call(['python', 'ros_packer.py', 'empty_dir'])
        self.assertEqual(return_val, 1)

        # Test mirror does not exists
        return_val = subprocess.call(['python', 'ros_packer.py', '-m no_mirror'])
        self.assertEqual(return_val, 2)

        # Test mirror is a Directory
        return_val = subprocess.call(['python', 'ros_packer.py', '-m empty_dir'])
        self.assertEqual(return_val, 2)


        # Test output already exists
        return_val = subprocess.call(['python', 'ros_packer.py', '-V 1', '-o file.ros', 'DIR_TO_PACK'])
        self.assertEqual(return_val, 1)

        # Test no mirror, no version, but DIR_TO_PACK
        return_val = subprocess.call(['python', 'ros_packer.py', 'DIR_TO_PACK'])
        self.assertEqual(return_val, 1)
