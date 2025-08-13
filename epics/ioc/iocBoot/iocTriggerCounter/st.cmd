#!../../bin/linux-x86_64/TriggerCounter

#- You may have to change TriggerCounter to something else
#- everywhere it appears in this file

< envPaths

## Register all support components
dbLoadDatabase "$(TOP)/dbd/TriggerCounter.dbd"
TriggerCounter_registerRecordDeviceDriver pdbbase

# Configure port
drvAsynSerialPortConfigure ("TriggerCounterPort", "/dev/ttyACM0")

## Load record instances
epicsEnvSet ("STREAM_PROTOCOL_PATH", "$(TOP)/db")
dbLoadRecords("$(TOP)/db/TriggerCounter.db","P=Timing:,R=TriggerCounter:,PORT=TriggerCounterPort")

cd "${TOP}/iocBoot/${IOC}"
iocInit

## Start any sequence programs
#seq sncxxx,"user=reinier"
