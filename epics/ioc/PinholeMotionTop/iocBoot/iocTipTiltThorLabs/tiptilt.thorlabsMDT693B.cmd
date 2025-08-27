#!../../bin/linux-x86_64/thorlabs

< envPaths

## Register all support components
dbLoadDatabase "$(TOP)/dbd/thorlabs.dbd"
thorlabs_registerRecordDeviceDriver pdbbase

cd "${TOP}/iocBoot/${IOC}"

## motorUtil (allstop & alldone)
dbLoadRecords("$(MOTOR)/db/motorUtil.db", "P=thorlabs:")

## 

drvAsynSerialPortConfigure("serial1", "/dev/ttyS0", 0, 0, 0)
asynOctetSetOutputEos("serial1",0,"\r")
asynOctetSetInputEos("serial1",0,"\r")

dbLoadTemplate("tiptilt.thorlabsMDT693B.substitutions")

# ThorLabs MDT695 Piezo - driver setup parameters:
#     (1) maximum number of controllers in system
#     (2) motor task polling rate (min=1Hz, max=60Hz)
MDT695Setup(1, 10)

# Thor driver configuration parameters:
#     (1) controller being configured
#     (2) asyn port name (string)
MDT695Config(0, "serial1")


iocInit

## motorUtil (allstop & alldone)
motorUtilInit("thorlabs:")

# Boot complete
