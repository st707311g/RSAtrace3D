# RSAtrace3D: a root system architecture vectorization software for monocot plants

![python](https://img.shields.io/badge/Python->3.10-lightgreen)
![developed_by](https://img.shields.io/badge/developed%20by-Shota_Teramoto-lightgreen)
![version](https://img.shields.io/badge/version-1.13-lightgreen)
![last_updated](https://img.shields.io/badge/last_update-June_1,_2023-lightgreen)

![GUI](./figures/RSAtrace3D.jpg)

## introduction

RSAtrace3D is a vectorization software to measure RSA (root system architecture) traits of monocot plants from 3D volume data such as X-ray CT images. Traits of  interest could be quantified by installing additional packages that could be freely designed by the users.

## system requirements

A mouse and keyboard are required for the operation. Windows and Linux are recommended because RSAtrace3D uses the `Delete` key. Since it draws an isocurve, it may be difficult to be seen on a high-resolution display, such as a retina display. The amount of memory usage depends on the size of the 3D image data handled. Version 3.6 or higher versions of Python must be installed.

RSAtrace3D depends on the following packages:

- PySide6==6.4.3 (6.5.0 doesnt work)
- pyqtgraph==0.13.3
- polars==0.17.9
- scikit-image==0.20.0
- scipy==1.10.1
- numpy==1.23.5
- pandas==2.0.1
- psutil==5.9.5
- coloredlogs==15.0.1

The following command will install the necessary packages.

```
pip install -U pip
pip install -r requirements.txt
```

The confirmed operating environments are shown below:

- CPU: Intel<sup>(R)</sup> Xeon<sup>(R)</sup> W-2295 CPU @ 3.00GHz
- Memory: 94 GB
- Ubuntu (20.04)
- Python (3.10.4)
    - PySide6==6.4.3 (6.5.0 doesnt work)
    - pyqtgraph==0.13.3
    - polars==0.17.9
    - scikit-image==0.20.0
    - scipy==1.10.1
    - numpy==1.23.5
    - pandas==2.0.1
    - psutil==5.9.5
    - coloredlogs==15.0.1

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
  * adjust: coding of some files (September 3, 2021)
* version 1.2 (February 17, 2022)
  * adjust: behavior of close-up in the slice view
  * adjust: coding of some files
* version 1.3 (August 12, 2022)
  * adjust: changed volume loading and saving behaviour
* version 1.4 (August 25, 2022)
  * update: supports tar.gz volume files
  * fix: types of string (November 29, 2022)
* version 1.5 (December 1, 2022)
  * update: `st_modules`
  * support: pyqtgraph latest version (0.13.1)
  * support: pyqt5 latest version (5.15.7)
* version 1.6 (December 12, 2022)
  * change: drawing algorithm for faster drawing
  * fix: bug (December 14, 2022)
* version 1.7 (December 16, 2022)
  * update: implementation of color dialog
  * update: implementation of intensity adjuster for projections
  * fix: typo
* version 1.8 (February 8, 2023)
  * fix: bug
  * remove: supports tar.gz volume files
* version 1.9 (February 8, 2023)
  * update: roots can be selected on the slice view (shift + double click).
  * fix: bug (February 9, 2023)
* version 1.10 (February 10, 2023)
  * update: support for multi roots.
* version 1.11 (February 22, 2023)
  * change: PyQt5 to PySide6
* version 1.12 (April 28, 2023)
  * support: polars latest version (0.17.9)
  * change: python version to 3.10
* version 1.13 (June 1, 2023)
  * support: multi CT images