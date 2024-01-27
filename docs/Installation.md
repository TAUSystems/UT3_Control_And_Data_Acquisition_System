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

# EPICS Base Installation

EPICS is designed to work on both regular PC OS and real-time OS. As, the UT3 CDAQ system relies on regular PCs, the instruction here will only address the installation process for Linux and Windows.

We provided a copy of EPICS base source in `epics/` but users can also choose to use their own installation if they have already installed `epics-base` on their system. In that case, users should modify the variables `${EPICS_BASE}` accordingly. 

## On Linux systems

To compile `epics-base` on Linux systems, you need GNU C++ compiler `g++` and GNU `make` tool. On Ubuntu, this can be installed with

```bash
sudo apt install build-essential
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

Please follow the EPICS documentation for installation on Windows machines. We will update this documentation at a later time.

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
#CAMAC=$(SUPPORT)/camac-R2-7-1
#CAPUTRECORDER=$(SUPPORT)/caputRecorder-R1-7-2
#DAC128V=$(SUPPORT)/dac128V-R2-9
DELAYGEN=$(SUPPORT)/delaygen-R1-2-4
#DXP=$(SUPPORT)/dxp-R6-0
#DXPSITORO=$(SUPPORT)/dxpSITORO-R1-2
DEVIOCSTATS=$(SUPPORT)/iocStats-3-1-16
#IP=$(SUPPORT)/ip-R2-20-1
IPAC=$(SUPPORT)/ipac-2-15
#IP330=$(SUPPORT)/ip330-R2-9
#IPUNIDIG=$(SUPPORT)/ipUnidig-R2-11
#LOVE=$(SUPPORT)/love-R3-2-7
#LUA=$(SUPPORT)/lua-R2-0
#MCA=$(SUPPORT)/mca-R7-8
#MEASCOMP=$(SUPPORT)/measComp-R2-3
#MODBUS=$(SUPPORT)/modbus-R3-0
MOTOR=$(SUPPORT)/motor-R7-3-1
#OPTICS=$(SUPPORT)/optics-R2-13-3
#QUADEM=$(SUPPORT)/quadEM-R9-2-1
#SOFTGLUE=$(SUPPORT)/softGlue-R2-8-2
#SOFTGLUEZYNQ=$(SUPPORT)/softGlueZynq-R2-0-2
SSCAN=$(SUPPORT)/sscan-R2-11-6
#STD=$(SUPPORT)/std-R3-6
STREAM=$(SUPPORT)/StreamDevice-2-8-24
#VAC=$(SUPPORT)/vac-R1-9
#VME=$(SUPPORT)/vme-R2-9-2
#YOKOGAWA_DAS=$(SUPPORT)/Yokogawa_DAS-R2-0-1
#XXX=$(SUPPORT)/xxx-R6-1
AREA_DETECTOR=$(SUPPORT)/areaDetector-R3-12-1
ADCORE=$(AREA_DETECTOR)/ADCore
ADSUPPORT=$(AREA_DETECTOR)/ADSupport
ADSIMDETECTOR=$(AREA_DETECTOR)/ADSimDetector
ADGENICAM=$(AREA_DETECTOR)/ADGenICam
ADSPINNAKER=$(AREA_DETECTOR)/ADSpinnaker
SNCSEQ=$(SUPPORT)/seq-2-2-6
#ALLEN_BRADLEY=$(SUPPORT)/allenBradley-2-3
```

To populate the `PATH` for the build to the subcomponent directories, run `make release`:
```
cd $HOME/UT3_Control_And_Data_Acquisition_System/epics/support
make release
```









