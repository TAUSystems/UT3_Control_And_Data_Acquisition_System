# UT3 Control and Data Acquisition System
The control and data acquisition system for the UT3 laser wakefield accelerator 
experiment.

It was developed by [TAU Systems Inc](https://www.tausystems.com) in collaboration 
with the UT3 group at the University of Texas at Austin. See [Authors](#authors) for more information.

## Overview
The UT3 C&DAQ system consists of several components:
* EPICS Control System
* Data acquisition & analysis
* User interface
* Storage

This repository contains code relating to the EPICS control system, and parts of 
the data acquisition and analysis, and part of the storage. The following details 
these items

### EPICS Control System
abcd

### Data Acquisition & Analysis
This part is itself divided into three components: 
* data uploader
* image backend
* image analysis complete handler

The *data uploader* is a client between the EPICS control system and the image 
backend and measurement database. It monitors process variables (PVs) in the EPICS 
IOCs containing images and scalars, and it uploads images to the image backend and
saves scalars to the measurement database. Its code is located in 
`epics/client/data_uploader`. See [its README](epics/client/data_uploader/README.md)
for more information.

The *image backend* is a standalone system to which images can be sent for 
analysis, and its results are stored on disk and in the measurement database. As 
a standalone system, it has [its own repository](https://github.com/TAUSystems/image-processing-backend).

The *image analysis complete handler* is a small client that listens for 
notifications from the image backend that analysis of certain images is complete, 
and it posts that information to EPICS PVs, which are picked up by the user 
interface. Its code is located in `epics/client/image_analysis_complete_handler`. 
See [its README](epics/client/image_analysis_complete_handler/README.md) for more 
information.

### User Interface
abcd

### Storage
abcd


## Installation & Usage

### EPICS Control System
See [EPICS installation](docs/Installation.md).

### Data Acquistion & Analysis
abcd

### User Interface
abcd



# Usage

## IOC start-up

## Control clients

## GUI Control clients

# Maintenance

## Bug Report and Issues

## Authors
This repository contains software developed through a collaboration involving personnel 
affiliated with TAU Systems and The University of Texas at Austin. Individual contributions 
were made by contributors acting in their respective employment or collaborative 
capacities.

The control system makes use of the [EPICS framework](https://epics-controls.org/)

### Primary Authors

- Reinier van Mourik <reinier.vanmourik@tausystems.com>
- Dung Duc Phan <brianp.dung@utexas.edu>

## Related Projects and Contributions

- [eSpecAnalysis](https://github.com/TAUSystems/eSpecAnalysis), by Thanh Ha
	<thanh.ha@tausystems.com>
- [User interface](https://github.com/TAUSystems/UT3_LabVIEW_2025), by Guillaume Plateau
	<guillaume.plateau@tausystems.com>
- [image processing backend](https://github.com/TAUSystems/image-processing-backend), by Reinier van Mourik
	<reinier.vanmourik@tausystems.com>

## History
In the early stage, this repository held the codebase of UT3 Control and DAQ (CDAQ) system written on TANGO framework. As Tau Systems moves toward EPICS, we transitioned the development of CDAQ to a new code base. Commit history and early release versions of TANGO-era are still available for access.
