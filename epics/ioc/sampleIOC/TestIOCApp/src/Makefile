TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = TestIOC
# TestIOC.dbd will be created and installed
DBD += TestIOC.dbd

# TestIOC.dbd will be made up from these files:
TestIOC_DBD += base.dbd

# Include dbd files from all support applications:
#TestIOC_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#TestIOC_LIBS += xxx

# TestIOC_registerRecordDeviceDriver.cpp derives from TestIOC.dbd
TestIOC_SRCS += TestIOC_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
TestIOC_SRCS_DEFAULT += TestIOCMain.cpp
TestIOC_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#TestIOC_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
TestIOC_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

