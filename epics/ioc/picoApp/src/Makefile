TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

DBD += PS3000A.dbd

LIBRARY_IOC += PS3000ASupport
PS3000ASupport_SRCS += PS3000A.cpp
PS3000ASupport_LIBS += asyn
PS3000ASupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================

ps3000a_DIR = $(PICO_SDK)/lib

PROD_IOC += PS3000A

# <name>_registerRecordDeviceDriver.cpp will be created from <name>.dbd
PS3000A_SRCS_DEFAULT += PS3000A_registerRecordDeviceDriver.cpp PS3000AMain.cpp
PS3000AVx_SRCS_vxWorks  += PS3000A_registerRecordDeviceDriver.cpp
PS3000A_INCLUDES += -I$(PICO_SDK)/include/libps3000a
PS3000A_LDFLAGS += -L$(PICO_SDK)/lib
PS3000A_LIBS += PS3000ASupport asyn
PS3000A_LIBS += ps3000a
PS3000A_LIBS += $(EPICS_BASE_IOC_LIBS)

ifeq ($(PICO_SDK),)
$(error "export PICO_SDK")
endif

PS3000A_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
