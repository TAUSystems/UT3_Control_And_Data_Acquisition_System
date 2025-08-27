TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

# The following are used for debugging messages.
#!USR_CXXFLAGS += -DDEBUG

#=============================
# Build the IOC application

PROD_IOC = thorlabs
# thorlabs.dbd will be created and installed
DBD += thorlabs.dbd

# thorlabs.dbd will be made up from these files:
thorlabs_DBD += base.dbd

# Include dbd files from all support applications:
#ifdef ASYN
thorlabs_DBD += asyn.dbd
thorlabs_DBD += drvAsynSerialPort.dbd
#endif
thorlabs_DBD += motorSupport.dbd
thorlabs_DBD += devThorLabs.dbd

# Add all the support libraries needed by this IOC
thorlabs_LIBS += ThorLabs
thorlabs_LIBS += motor
#ifdef ASYN
thorlabs_LIBS += asyn
#endif
#ifdef SNCSEQ
thorlabs_LIBS += seq pv
#endif

# thorlabs_registerRecordDeviceDriver.cpp derives from thorlabs.dbd
thorlabs_SRCS += thorlabs_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
thorlabs_SRCS_DEFAULT += thorlabsMain.cpp
thorlabs_SRCS_vxWorks += -nil-

# Add PVAccess support
# https://epics.anl.gov/tech-talk/2024/msg00460.php
# QSRV2
ifdef PVXS_MAJOR_VERSION # prefer QSRV2 :)
zaberMotion_DBD += pvxsIoc.dbd
zaberMotion_LIBS += pvxsIoc pvxs
else
ifdef EPICS_QSRV_MAJOR_VERSION # fallback to QSRV1
zaberMotion_LIBS += qsrv
zaberMotion_LIBS += $(EPICS_BASE_PVA_CORE_LIBS)
zaberMotion_DBD += PVAServerRegister.dbd
zaberMotion_DBD += qsrv.dbd
endif
endif


# Add support from base/src/vxWorks if needed
#thorlabs_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
thorlabs_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

