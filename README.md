# RSAtrace3D: a root system architecture vectorization software for monocot plants

![python](https://img.shields.io/badge/Python->3.8-lightgreen)
![developed_by](https://img.shields.io/badge/developed%20by-Shota_Teramoto-lightgreen)
![version](https://img.shields.io/badge/version-1.3-lightgreen)
![last_updated](https://img.shields.io/badge/last_update-August_12,_2022-lightgreen)

![GUI](./figures/RSAtrace3D.jpg) 

## introduction

RSAtrace3D is a vectorization software to measure RSA (root system architecture) traits of monocot plants from 3D volume data such as X-ray CT images. Traits of  interest could be quantified by installing additional packages that could be freely designed by the users.

## system requirements

A mouse and keyboard are required for the operation. Windows and Linux are recommended because RSAtrace3D uses the `Delete` key. Since it draws an isocurve, it may be difficult to be seen on a high-resolution display, such as a retina display. The amount of memory usage depends on the size of the 3D image data handled. Version 3.6 or higher versions of Python must be installed.

RSAtrace3D depends on the following packages:

- numpy
- scipy
- scikit-image
- pandas
- PyQt5
- pyqtgraph (Version 0.12.2 does not work. Use version <= 0.12.1)
- psutil

The following command will install the necessary packages.

```
pip install -U pip
pip install -r requirements.txt
```

The confirmed operating environments are shown below:

Environment 1:

- CPU: Intel<sup>(R)</sup> Core<sup>(TM)</sup> i7-8700 CPU @ 3.20 GHz
- Memory: 32 GB
- Ubuntu (18.04.4 LTS)
- Python (3.6.9)
    - numpy (1.18.4)
    - scipy (1.4.1)
    - scikit-image (0.17.1)
    - pandas (1.1.0)
    - PyQt5 (5.14.2)
    - pyqtgraph (0.10.0)
    - psutil (5.7.0)

Environment 2:

- CPU: Intel<sup>(R)</sup> Core<sup>(TM)</sup> i7-8700 CPU @ 3.20 GHz
- Memory: 32 GB
- Ubuntu (18.04.4 LTS)
- Python (3.8.2)
    - numpy (1.20.3)
    - scipy (1.6.3)
    - scikit-image (0.18.1)
    - pandas (1.2.4)
    - PyQt5 (5.14.2)
    - pyqtgraph (0.12.1)
    - psutil (5.8.0)

## installation

Run the following commands:

```
git clone https://github.com/st707311g/RSAtrace3D.git
cd RSAtrace3D
```

## how to use

A manual file is avairable [here](./manual/how_to_use.md).

## version policy

Version information consists of major and minor versions (major.minor). When the major version increases by one, it is no longer compatible with the original version. When the minor version invreases by one, compatibility will be maintained. Revisions that do not affect functionality, such as bug fixes and design changes, will not affect the version number.

## citation

Please cite the following article:

Shota Teramoto et al. RSAtrace3D: robust vectorization software for measuring monocot root system architecture (2021) BMC plant biol. in press.

## license

NARO NON-COMMERCIAL LICENSE AGREEMENT Version 1.0

This license is for 'Non-Commercial' use of software for RSAtrace3D

* Scientific use of RSAtrace3D is permitted free of charge.
* Modification of RSAtrace3D is only permitted to the person of downloaded and his/her colleagues.
* The National Agriculture and Food Research Organization (hereinafter referred to as NARO) does not guarantee that defects, errors or malfunction will not occur with respect to RSAtrace3D.
* NARO shall not be responsible or liable for any damage or loss caused or be alleged to be caused, directly or indirectly, by the download and use of RSAtrace3D.
* NARO shall not be obligated to correct or repair the program regardless of the extent, even if there are any defects of malfunctions in RSAtrace3D.
* The copyright and all other rights of RSAtrace3D belong to NARO.
* Selling, renting, re-use of license, or use for business purposes etc. of RSAtrace3D shall not be allowed. For commercial use, license of commercial use is required. Inquiries for such commercial license are directed to NARO.
* The RSAtrace3D may be changed, or the distribution maybe canceled without advance notification.
*In case the result obtained using RSAtrace3D in used for publication in academic journals etc., please refer the publication of RSAtrace3D and/or acknowledge the use of RSAtrace3D in the publication.

Copyright (C) 2020 National Agriculture and Food Research Organization. All rights reserved.

## project homepage
https://rootomics.dna.affrc.go.jp/en/

## update history

* version 1.0 (Jan 6, 2021)
  * initial version uploaded
* version 1.1 (June 4, 2021)
  * update: mod - traits
  * install: mod - traits debug function
  * install: projection view slice line
  * install: manual
  * fix: behavior when the spacebar is pressed
  * fix: running the program under Windows 10 (July 15, 2021)
  * fix: importing mod modules (August 11, 2021)
  * adjust: coding of some files (September, 3, 2021)
* version 1.2 (February, 17, 2022)
  * adjust: behavior of close-up in the slice view
  * adjust: coding of some files
* version 1.3 (August, 12, 2022)
  * adjust: changed volume loading and saving behaviour