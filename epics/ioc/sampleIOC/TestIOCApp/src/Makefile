TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS BELOW HERE

# Use typed rset structure (see 3.16.1 release notes)
USR_CPPFLAGS += -DUSE_TYPED_RSET

# xxxRecord.h will be created from xxxRecord.dbd
DBDINC += xxxRecord

# Install xxxSupport.dbd into <top>/dbd
DBD += xxxSupport.dbd

# Build an IOC support library
LIBRARY_IOC += TestIOCSupport

# Compile and add code to the support library
TestIOCSupport_SRCS += xxxRecord.c
TestIOCSupport_SRCS += devXxxSoft.c

# Link locally-provided code into the support library,
# rather than directly into the IOC application, that
# causes problems on Windows DLL builds
TestIOCSupport_SRCS += dbSubExample.c
TestIOCSupport_SRCS += devTestIOCVersion.c
TestIOCSupport_SRCS += TestIOCHello.c
TestIOCSupport_SRCS += initTrace.c

TestIOCSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

# Auto-generate a header file containing a version string.
# Version comes from the VCS if available, else date+time.
GENVERSION = TestIOCVersion.h
# Macro name
GENVERSIONMACRO = TestIOCVERSION

# Build the IOC application
PROD_IOC = TestIOC

# TestIOC.dbd will be created and installed
DBD += TestIOC.dbd

# TestIOC.dbd will include these files:
TestIOC_DBD += base.dbd
TestIOC_DBD += xxxSupport.dbd
TestIOC_DBD += dbSubExample.dbd
TestIOC_DBD += devTestIOCVersion.dbd
TestIOC_DBD += TestIOCHello.dbd
TestIOC_DBD += initTrace.dbd

# TestIOC_registerRecordDeviceDriver.cpp derives from TestIOC.dbd
TestIOC_SRCS += TestIOC_registerRecordDeviceDriver.cpp

# Build the main IOC entry point where needed
TestIOC_SRCS_DEFAULT += TestIOCMain.cpp
TestIOC_SRCS_vxWorks += -nil-

# Link in the code from our support library
TestIOC_LIBS += TestIOCSupport

# To build SNL programs, SNCSEQ must be defined
# in the <top>/configure/RELEASE file
ifneq ($(SNCSEQ),)
    # Build sncExample into TestIOCSupport
    sncExample_SNCFLAGS += +r
    TestIOC_DBD += sncExample.dbd
    # A .stt sequence program is *not* pre-processed:
    TestIOCSupport_SRCS += sncExample.stt
    TestIOCSupport_LIBS += seq pv
    TestIOC_LIBS += seq pv

    # Build sncProgram as a standalone program
    PROD_HOST += sncProgram
    sncProgram_SNCFLAGS += +m
    # A .st sequence program *is* pre-processed:
    sncProgram_SRCS += sncProgram.st
    sncProgram_LIBS += seq pv
    sncProgram_LIBS += $(EPICS_BASE_HOST_LIBS)
endif

# Link QSRV (pvAccess Server) if available
ifdef EPICS_QSRV_MAJOR_VERSION
    TestIOC_LIBS += qsrv
    TestIOC_LIBS += $(EPICS_BASE_PVA_CORE_LIBS)
    TestIOC_DBD += PVAServerRegister.dbd
    TestIOC_DBD += qsrv.dbd
endif

# Finally link IOC to the EPICS Base libraries
TestIOC_LIBS += $(EPICS_BASE_IOC_LIBS)

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD EXTRA GNUMAKE RULES BELOW HERE

# Explicit dependency needed for generated header file
devTestIOCVersion$(DEP): $(COMMON_DIR)/$(GENVERSION)
