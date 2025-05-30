#!../../bin/linux-x86_64/GentecIntegra

#- You may have to change GentecIntegra to something else
#- everywhere it appears in this file

< envPaths

## Register all support components
dbLoadDatabase "../../dbd/GentecIntegra.dbd"
GentecIntegra_registerRecordDeviceDriver pdbbase

# Configure Energy Meter port
epicsEnvSet ("STREAM_PROTOCOL_PATH", "../../db")

drvAsynSerialPortConfigure ("EnergyMeter1","/dev/ttyACM0")

## Load record instances
dbLoadRecords("../../db/GentecIntegra.db","P=Laser:,R=Energy:,PORT=EnergyMeter1")

iocInit

## Start any sequence programs
#seq sncxxx,"user=reinier"
