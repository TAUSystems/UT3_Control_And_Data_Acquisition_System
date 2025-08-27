#!../../bin/linux-x86_64/thorlabs

< envPaths

## Register all support components
dbLoadDatabase "$(TOP)/dbd/thorlabs.dbd"
thorlabs_registerRecordDeviceDriver pdbbase

cd "${TOP}/iocBoot/${IOC}"

## motorUtil (allstop & alldone)
dbLoadRecords("$(MOTOR)/db/motorUtil.db", "P=thorlabs:")

## 
# 3-axis piezo controller for xxx, xxx, and xxx
drvAsynSerialPortConfigure("PinholeMTD693B", "/dev/ttyS0", 0, 0, 0)
asynOctetSetOutputEos("PinholeMTD693B",0,"\r")
asynOctetSetInputEos("PinholeMTD693B",0,"\r")

# 1-axis piezo controller for xxx
drvAsynSerialPortConfigure("PinholeMTD694B", "/dev/ttyS1", 0, 0, 0)
asynOctetSetOutputEos("PinholeMTD694B",0,"\r")
asynOctetSetInputEos("PinholeMTD694B",0,"\r")


# ThorLabs MDT695 Piezo - driver setup parameters:
#     (1) maximum number of controllers in system
#     (2) motor task polling rate (min=1Hz, max=60Hz)
MDT695Setup(2, 10)

# Thor driver configuration parameters:
#     (1) controller being configured
#     (2) asyn port name (string)
MDT695Config(0, "PinholeMTD693B")
MDT695Config(1, "PinholeMTD694B")

dbLoadTemplate("tiptilt.thorlabsMDT693B.substitutions")

iocInit

## motorUtil (allstop & alldone)
motorUtilInit("thorlabs:")

# Boot complete
