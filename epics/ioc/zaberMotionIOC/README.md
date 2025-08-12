# Zaber motion IOC
IOC to control Zaber motorized stages, using the EPICS motor module. See 
[README on GitHub](https://github.com/zabertech/motorZaberMotion). This README 
has some additional installation instructions for use at UT3. 

The repository contains a motor module that can be installed within the 
EPICS motor support or as a standalone library. It comes with an IOC that uses 
the library, and again the IOC can be installed within the library or as a 
standalone. 

For the purposes of separating support from IOCs, I've chosen to install the 
library within the EPICS motor support, and the IOC under epics/ioc/ in this 
repository. 

## Library Installation
1. Clone the [v1.0.1 tag](https://github.com/zabertech/motorZaberMotion/tree/v1.0.1) 
   from the motorZaberMotion repository into $(MOTOR)/modules (the top of the main 
   branch in August 2025 has a bug that mislocates the library to find libmotor.a). 
   My other support modules were motor-R7-3-1 (R7-1 fails to compile) and asyn-R4-44-2. 
1. Edit $(MOTOR)/modules/Makefile to select which motor modules to include in the 
   make. I added the motorZaberMotion module in a separate Makefile.local.
1. As usual, update the $(MOTOR)/configure/RELEASE file (or add a RELEASE.local) 
   to point to EPICS_BASE and support modules. Since the idea is to build the IOC 
   separately, don't add BUILD_IOC = YES from EXAMPLE_CONFIG_SITE.
1. Run `make` in the $(MOTOR) directory.

## IOC build
Presumably you could set BUILD_IOC = YES from EXAMPLE_CONFIG_SITE, and then copy 
the IOC from the support module into our UT3 repository. However, building separately 
allows adding PVXS for example, and sets env_paths correctly.

1. Copy the zaberMotionIOC into the ioc repository. 
1. Add ASYN, SEQ, MOTOR, and EPICS_BASE to zaberMotionIOC/configure/RELEASE.local. 
   Add PVXS as well, if desired.
1. Run `make` in the zaberMotionIOC directory.
1. Update motor.cmd.zaber and motor.substitutions.zaber in iocBoot/iocZaberMotion




