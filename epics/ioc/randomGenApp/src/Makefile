TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = randomGen
# randomGen.dbd will be created and installed
DBD += randomGen.dbd

# randomGen.dbd will be made up from these files:
randomGen_DBD += base.dbd

# Include dbd files from all support applications:
randomGen_DBD += devAiRnd.dbd

# Add all the support libraries needed by this IOC
#randomGen_LIBS += xxx

# randomGen_registerRecordDeviceDriver.cpp derives from randomGen.dbd
randomGen_SRCS += randomGen_registerRecordDeviceDriver.cpp

randomGen_SRCS += devAiRnd.c
randomGen_SRCS += drvRandom.c

# Build the main IOC entry point on workstation OSs.
randomGen_SRCS_DEFAULT += randomGenMain.cpp
randomGen_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#randomGen_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
randomGen_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

