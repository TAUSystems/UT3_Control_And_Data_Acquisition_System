#!../../bin/linux-x86_64/TriggerCounter

#- You may have to change TriggerCounter to something else
#- everywhere it appears in this file

< envPaths

## Register all support components
dbLoadDatabase "$(TOP)/dbd/TriggerCounter.dbd"
TriggerCounter_registerRecordDeviceDriver pdbbase

# Configure port
drvAsynSerialPortConfigure ("TriggerCounterPort", "/dev/serial/by-id/usb-Texas_Instruments_In-Circuit_Debug_Interface_0E20076B-if00")
asynSetOption("TriggerCounterPort", 0, "baud", "115200")
asynSetOption("TriggerCounterPort", 0, "bits", "8")
asynSetOption("TriggerCounterPort", 0, "stop", "1")
asynSetOption("TriggerCounterPort", 0, "parity", "none")
asynSetOption("TriggerCounterPort", 0, "ixon", "Y")

## Load record instances
epicsEnvSet ("STREAM_PROTOCOL_PATH", "$(TOP)/db")
dbLoadRecords("$(TOP)/db/TriggerCounter.db","P=Timing:,R=TriggerCounter:,PORT=TriggerCounterPort")

cd "${TOP}/iocBoot/${IOC}"
iocInit

## Start any sequence programs
#seq sncxxx,"user=reinier"
