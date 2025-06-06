TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = GentecIntegra
# GentecIntegra.dbd will be created and installed
DBD += GentecIntegra.dbd

# GentecIntegra.dbd will be made up from these files:
GentecIntegra_DBD += base.dbd

# Include dbd files from all support applications:
GentecIntegra_DBD += asyn.dbd
GentecIntegra_DBD += drvAsynSerialPort.dbd
GentecIntegra_DBD += calcSupport.dbd # stream.dbd needs scalcout
GentecIntegra_DBD += stream.dbd

# Add all the support libraries needed by this IOC
GentecIntegra_LIBS += calc
GentecIntegra_LIBS += stream
GentecIntegra_LIBS += asyn

# GentecIntegra_registerRecordDeviceDriver.cpp derives from GentecIntegra.dbd
GentecIntegra_SRCS += GentecIntegra_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
GentecIntegra_SRCS_DEFAULT += GentecIntegraMain.cpp
GentecIntegra_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#GentecIntegra_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
GentecIntegra_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

