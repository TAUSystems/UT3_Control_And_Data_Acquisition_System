TOP=../..
include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE

PROD_NAME = spinnakerApp
PROD_IOC_WIN32 += $(PROD_NAME)
PROD_IOC_Linux += $(PROD_NAME)

# <name>.dbd will be created from <name>Include.dbd
DBD += $(PROD_NAME).dbd
$(PROD_NAME)_DBD += ADSpinnakerSupport.dbd

# <name>_registerRecordDeviceDriver.cpp will be created from <name>.dbd
$(PROD_NAME)_SRCS += $(PROD_NAME)_registerRecordDeviceDriver.cpp $(PROD_NAME)Main.cpp

# Add locally compiled object code
PROD_LIBS += ADSpinnaker
ifeq (debug, $(findstring debug, $(T_A)))
  PROD_LIBS_WIN32 += Spinnakerd_v140
else
  PROD_LIBS_WIN32 += Spinnaker_v140
endif

PROD_LIBS += ADGenICam

# We use PROD_SYS_LIBS even though libflycapture.so is in the ADSpinnaker tree 
# because we are doing static build but the file is a .so file, not a .a file.
PROD_SYS_LIBS_Linux += Spinnaker
PROD_SYS_LIBS_Linux += GCBase_gcc540_v3_0
PROD_SYS_LIBS_Linux += GenApi_gcc540_v3_0
PROD_SYS_LIBS_Linux += NodeMapData_gcc540_v3_0
PROD_SYS_LIBS_Linux += MathParser_gcc540_v3_0
PROD_SYS_LIBS_Linux += XmlParser_gcc540_v3_0
PROD_SYS_LIBS_Linux += Log_gcc540_v3_0

include $(ADCORE)/ADApp/commonDriverMakefile


# Add PVAccess support
# https://epics.anl.gov/tech-talk/2024/msg00460.php
# QSRV2
ifdef PVXS_MAJOR_VERSION # prefer QSRV2 :)
$(PROD_NAME)_DBD += pvxsIoc.dbd
$(PROD_NAME)_LIBS += pvxsIoc pvxs
else
ifdef EPICS_QSRV_MAJOR_VERSION # fallback to QSRV1
$(PROD_NAME)_LIBS += qsrv
$(PROD_NAME)_LIBS += $(EPICS_BASE_PVA_CORE_LIBS)
$(PROD_NAME)_DBD += PVAServerRegister.dbd
$(PROD_NAME)_DBD += qsrv.dbd
endif
endif



#=============================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

