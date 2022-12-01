# A set of general-purpose modules for 3D image processing.

![python](https://img.shields.io/badge/Python->3.8-lightgreen)
![developed_by](https://img.shields.io/badge/developed%20by-Shota_Teramoto-lightgreen)
![version](https://img.shields.io/badge/version-1.1-lightgreen)
![last_updated](https://img.shields.io/badge/last_update-November_15,_2022-lightgreen)

## modules

- volume.py (handling 3D volumes)
  - Volume3D (A class for handling a 3D volume)
  - VolumeLoader (A class for 3D volume loading)
  - VolumeSaver (A class for 3D volume saving)
  - VolumeSeparator (A class for 3D volume separating and assembling)
- seek.py (listing files and directories)
  - walk_to_find_directories (A function returning the generator generating the subdirectory paths)
  - walk_to_find_files (A function returning the generator generating the file paths)

## version policy

Version information consists of major and minor versions (major.minor). When the major version increases by one, it is no longer compatible with the original version. When the minor version invreases by one, compatibility will be maintained. Revisions that do not affect functionality, such as bug fixes and design changes, will not affect the version number.

## project homepage
https://rootomics.dna.affrc.go.jp/en/

## update history

- version 1.0 (Oct 14, 2022)
  - initial version uploaded
- version 1.1 (Nov 15, 2022)
  - type fix
  - added the parameter `including_source_directoriy` into the `walk_to_find_directories` function.