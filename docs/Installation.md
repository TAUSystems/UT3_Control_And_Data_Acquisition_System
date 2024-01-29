# Getting source code

GitHub: [UT3 Control and Data Acquisition](https://github.com/TAUSystems/UT3_Control_And_Data_Acquisition_System). Need Tau Systems credentials (ask Reinier) to access the source code.

Please install `git` on your system before going forward.

```bash
cd $HOME
git clone --recursive git@github.com:TAUSystems/UT3_Control_And_Data_Acquisition_System.git
```

For deployment where you don't need to change the code, you can use the https
```bash
cd $HOME
git clone --recursive https://github.com/TAUSystems/UT3_Control_And_Data_Acquisition_System.git
```

Notice that in this instruction, the source is cloned to `$HOME` for simplicity. Users can install this source repo to any location on your system, as long as they make sure to set the `${EPICS_BASE}` and `${SUPPORT}` paths correspondingly.

# EPICS Base Installation

EPICS is designed to work on both regular PC OS and real-time OS. As, the UT3 CDAQ system relies on regular PCs, the instruction here will only address the installation process for Linux and Windows.

We provided a copy of EPICS base source in `epics/` but users can also choose to use their own installation if they have already installed `epics-base` on their system. In that case, users should modify the variables `${EPICS_BASE}` accordingly. 

## On Linux systems

To compile `epics-base` on Linux systems, you need GNU C++ compiler `g++` and GNU `make` tool. `re2c` is needed for `sequencer` and `streamDevice`. On Ubuntu, these packages can be installed with

```bash
sudo apt install build-essential re2c
```

To compile
```bash
cd $HOME/UT3_Control_And_Data_Acquisition_System/epics/epics-base
make
```

Put these lines in the `bashrc` or `zshrc` config files
```bash
export EPICS_PATH=$HOME/UT3_Control_And_Data_Acquisition_System/epics
export EPICS_BASE=${EPICS_PATH}/epics-base
export EPICS_SUPPORT=${EPICS_PATH}/support
export EPICS_HOST_ARCH=$(${EPICS_BASE}/startup/EpicsHostArch)
export PATH=${EPICS_BASE}/bin/${EPICS_HOST_ARCH}:${PATH}
```

Testing the build by open a new terminal and run `softIoc`. If encountering no problem, the installation is done.

## On Windows systems

For the moment, please follow the EPICS documentation for installation on Windows machines. We will update this documentation for Windows at a later time.

# EPICS Modules and IOCs

For UT3 CDAQ, we need the controllers for:
- FLIR GigE cameras (BFLY-PGE-31S4MC).
- Thorlabs DC servo motor and motor controller (Kinesis KDC-101).
- Stanford Research System delay generators (DG645 and DG535).
- Mensor pressure controller (CPC6050).
- NI DAQ I/O USB 2.0.

The cameras, motor and motor controller, delay generator are EPICS ready. The pressure controller and NI DAQ need custom IOCs (Guillaume implemented in LabView).

In this section, we will install the EPICS modules needed for UT3's devices.

## Support Modules

Among other things, support modules handle the interactions between IOC **process database** and the hardware's drivers. A collection of these modules has been provided by [`synApps`](https://www.aps.anl.gov/BCDA/synApps). In this repo, we restructured the directories for simplicity: all the `synApps` modules are in `epics/support`. 

The following modules are needed for UT3 CDAQ:
- ALIVE
- ASYN
- AUTOSAVE
- BUSY
- CALC
- DEVIOCSTATS
- IPAC
- SSCAN
- STREAM
- AREA_DETECTOR
	- ADCORE
	- ADSUPPORT
	- ADGENICAM
	- ADSPINNAKER
	- PVADRIVER
- MOTOR
	- MOTOR_THORLABS
- SNCSEQ

In `epicss/support/configure/RELEASE`, modify the `SUPPORT` and `EPICS_BASE` variables to be the absolute path to the `support` and the `epics-base` installation, respectively:
```
SUPPORT=/absolute/path/to/support/
-include $(TOP)/configure/SUPPORT.$(EPICS_HOST_ARCH)
EPICS_BASE=/absolute/path/to/epics/base
-include $(TOP)/configure/EPICS_BASE
-include $(TOP)/configure/EPICS_BASE.$(EPICS_HOST_ARCH)
```

Comment out the packages that are not needed for the build:
```
ALIVE=$(SUPPORT)/alive-R1-1-1
ASYN=$(SUPPORT)/asyn-R4-44-2
AUTOSAVE=$(SUPPORT)/autosave-R5-10
BUSY=$(SUPPORT)/busy-R1-7-2
CALC=$(SUPPORT)/calc-R3-7-3
DELAYGEN=$(SUPPORT)/delaygen-R1-2-4
DEVIOCSTATS=$(SUPPORT)/iocStats-3-1-16
IPAC=$(SUPPORT)/ipac-2-15
MOTOR=$(SUPPORT)/motor-R7-3-1
MOTOR_THORLABS=$(MOTOR)/modules/motorThorLabs-R1-0-2
SNCSEQ=$(SUPPORT)/seq-2-2-6
SSCAN=$(SUPPORT)/sscan-R2-11-6
STREAM=$(SUPPORT)/StreamDevice-2-8-24

AREA_DETECTOR=$(SUPPORT)/areaDetector
ADCORE=$(AREA_DETECTOR)/ADCore
ADSUPPORT=$(AREA_DETECTOR)/ADSupport
ADSIMDETECTOR=$(AREA_DETECTOR)/ADSimDetector
ADGENICAM=$(AREA_DETECTOR)/ADGenICam
ADSPINNAKER=$(AREA_DETECTOR)/ADSpinnaker
PVADRIVER=$(AREA_DETECTOR)/pvaDriver
NDDRIVERSTDARRAYS=$(AREA_DETECTOR)/NDDriverStdArrays
```

To populate the `PATH` for the build to the subcomponent directories, run `make release`:
```bash
cd $HOME/UT3_Control_And_Data_Acquisition_System/epics/support
make release
```

To start build most of the modules
```bash
cd $HOME/UT3_Control_And_Data_Acquisition_System/epics/support
make
```

To build the Thorlabs motor module:
```bash
cd $HOME/UT3_Control_And_Data_Acquisition_System/epics/support/motor-R7-3-1/modules/motorThorLabs-R1-0-2
make
```

## IOCs

The IOCs are packaged with these modules. For the `areaDetector` module, users need to select the option `BUILD_IOCS=YES` in the `$(TOP)/configure/CONFIG_SITE.local`.

# Maintenance

To upgrade the modules, we recommend to use `.tar.gz` files from the GitHub release pages. 

# References:

1. [synApps | Advanced Photon Source](https://www.aps.anl.gov/BCDA/synApps)
2. [Installation on Linux / MacOS — EPICS Documentation documentation](https://docs.epics-controls.org/en/latest/getting-started/installation-linux.html#install-epics)
3. [GitHub - epics-modules/sscan: APS BCDA synApps module: sscan](https://github.com/epics-modules/sscan)
4. [GitHub - areaDetector/areaDetector: Top-level repository for the EPICS areaDetector project](https://github.com/areaDetector/areaDetector)


