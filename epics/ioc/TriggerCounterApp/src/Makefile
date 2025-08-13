TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = TriggerCounter
# TriggerCounter.dbd will be created and installed
DBD += TriggerCounter.dbd

# TriggerCounter.dbd will be made up from these files:
TriggerCounter_DBD += base.dbd

# Include dbd files from all support applications:
TriggerCounter_DBD += asyn.dbd
TriggerCounter_DBD += drvAsynSerialPort.dbd
TriggerCounter_DBD += calcSupport.dbd # stream.dbd needs scalcout
TriggerCounter_DBD += stream.dbd

# Add all the support libraries needed by this IOC
TriggerCounter_LIBS += calc
TriggerCounter_LIBS += stream
TriggerCounter_LIBS += asyn

# TriggerCounter_registerRecordDeviceDriver.cpp derives from TriggerCounter.dbd
TriggerCounter_SRCS += TriggerCounter_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
TriggerCounter_SRCS_DEFAULT += TriggerCounterMain.cpp
TriggerCounter_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#TriggerCounter_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
TriggerCounter_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

