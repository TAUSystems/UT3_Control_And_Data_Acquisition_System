TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = Timing
# Timing.dbd will be created and installed
DBD += Timing.dbd

# Timing.dbd will be made up from these files:
Timing_DBD += base.dbd

# Include dbd files from all support applications:
#Timing_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#Timing_LIBS += xxx

# Timing_registerRecordDeviceDriver.cpp derives from Timing.dbd
Timing_SRCS += Timing_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
Timing_SRCS_DEFAULT += TimingMain.cpp
Timing_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#Timing_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
Timing_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

