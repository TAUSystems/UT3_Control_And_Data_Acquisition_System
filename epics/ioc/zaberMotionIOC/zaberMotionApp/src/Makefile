TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

# The following are used for debugging messages.
#!USR_CXXFLAGS += -DDEBUG

#=============================
# Build the IOC application

# This module must be built with c++17
USR_CXXFLAGS += -std=c++17

PROD_IOC = zaberMotion
# zaberMotion.dbd will be created and installed
DBD += zaberMotion.dbd

# zaberMotion.dbd will be made up from these files:
zaberMotion_DBD += base.dbd

# Include dbd files from all support applications:
#ifdef ASYN
zaberMotion_DBD += asyn.dbd
zaberMotion_DBD += drvAsynSerialPort.dbd
#endif
zaberMotion_DBD += motorSupport.dbd
zaberMotion_DBD += zaberMotionSupport.dbd

# Add all the support libraries needed by this IOC
zaberMotion_LIBS += ZaberMotion
zaberMotion_LIBS += motor
#ifdef ASYN
zaberMotion_LIBS += asyn
#endif
#ifdef SNCSEQ
zaberMotion_LIBS += seq pv
#endif

# zaberMotion_registerRecordDeviceDriver.cpp derives from zaberMotion.dbd
zaberMotion_SRCS += zaberMotion_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
zaberMotion_SRCS_DEFAULT += zaberMotionMain.cpp
zaberMotion_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#zaberMotion_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
zaberMotion_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

