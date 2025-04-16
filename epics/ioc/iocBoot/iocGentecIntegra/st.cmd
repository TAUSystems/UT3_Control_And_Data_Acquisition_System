#!../../bin/linux-x86_64/GentecIntegra

#- You may have to change GentecIntegra to something else
#- everywhere it appears in this file

< envPaths

## Register all support components
dbLoadDatabase "../../dbd/GentecIntegra.dbd"
GentecIntegra_registerRecordDeviceDriver pdbbase

# Configure Energy Meter port
epicsEnvSet ("STREAM_PROTOCOL_PATH", "../../db")

drvAsynSerialPortConfigure ("EnergyMeter1","/dev/ttyS1")
asynSetOption ("EnergyMeter1", 0, "baud", "9600")
asynSetOption ("EnergyMeter1", 0, "bits", "8")
asynSetOption ("EnergyMeter1", 0, "parity", "none")
asynSetOption ("EnergyMeter1", 0, "stop", "1")
asynSetOption ("EnergyMeter1", 0, "clocal", "Y")
asynSetOption ("EnergyMeter1", 0, "crtscts", "N")

## Load record instances
dbLoadRecords("../../db/GentecIntegra.db","P=Laser,R=Energy,PORT=EnergyMeter1")

iocInit

## Start any sequence programs
#seq sncxxx,"user=reinier"
