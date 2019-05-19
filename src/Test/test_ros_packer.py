from Code.ros_packer import check_input, check_dir, pack_ros
from Code.ros_header_v1 import ros_header_v1
from Code.ros_payload_header import ros_payload_header



header = ros_header_v1('LS23','1.01', 52, 46, 11, 20, 3, 2007, 5)

print(header.arc_magic.hex())
print(header.arc_index.hex())
print(header.time_stamp.hex())
print(header.checksum.hex())
print(header.signature.hex())
print(header.unknown1.hex())
print(header.dir_entries.hex())
print(header.unknown1.hex())

print(header.get_bytes().hex())
print(header.__sizeof__())

dir_header = ros_payload_header('CLI_FILE2', 208, 106734)
print(dir_header.get_bytes().hex())
print(dir_header.__sizeof__())
