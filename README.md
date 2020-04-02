# ROS PACKER

Packer for the ros firmware container format

## Description

This Python project is the inversion of [ros_pack](https://github.com/iam-TJ/ros_pack "Iam-TJ's ros_pack") written by Iam-TJ. Unfortunately, his project is not being maintained anymore.
The state of the given reverse engineering has not being touched, but **ros_packer** supports mirroring for copying unknown Bytes.

This project was developed in conjunction with the [Fraunhofer FKIE Institute](https://www.fkie.fraunhofer.de/) within a firmware security lab.

## What is ROS?

`*.ros`-files are commonly used as Firmware-format on routers, switches etc. They are also used as firmware upgrade media and usually carry the whole software on such devices. The structure of a `*.ros`-file consists of several payloads, that come with headers and subheaders.


## Features

**ros-packer** has two major ways to use:  
**A**: you can define which header version (Version 1 or 2) is being used during the packing process.  
**B**: you can use a ros-file as reference. This auto detects the header version and copies unknown bytes.

*  supports two header versions
*  copy unknown bytes from a reference container
*  take over header version from a reference container
*  set output file name
*  calculating checksums



## Installation

1.  Make sure you have a working **Python3.X** environment.
2.  Clone the project `git clone https://gitlab.com/m-rtz/ros-packer`

## Using

`ros_packer.py [-h] [-v] [-o OUTPUT] [-m MIRROR | -V {1,2}] DIR_TO_PACK`
*  -h:  shows this help
*  -V:  selects the header version (1 or 2). If -m is not used.
*  -m:  selects a reference container. If -V ist not used.
*  -o:  selects a file name of the output container.
*  -v:  shows verbosity messages

### Example
`ros_packer -m reference_container.ros -o output_container.ros ./Payload_Dir` 

This creates a new container file named `output_container.ros` form all payload files in `./Payload_Dir`. To determine the header version and copy unknown bytes the reference container `reference_container.ros` is being read.