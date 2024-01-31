TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = TakeNShots
# TakeNShots.dbd will be created and installed
DBD += TakeNShots.dbd

# TakeNShots.dbd will be made up from these files:
TakeNShots_DBD += base.dbd

# Include dbd files from all support applications:
#TakeNShots_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#TakeNShots_LIBS += xxx

# TakeNShots_registerRecordDeviceDriver.cpp derives from TakeNShots.dbd
TakeNShots_SRCS += TakeNShots_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
TakeNShots_SRCS_DEFAULT += TakeNShotsMain.cpp
TakeNShots_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#TakeNShots_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
TakeNShots_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

