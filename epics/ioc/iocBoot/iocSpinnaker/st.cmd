#!../../bin/linux-x86_64/Spinnaker

#- You may have to change Spinnaker to something else
#- everywhere it appears in this file

< envPaths

cd "${TOP}"

## Register all support components
dbLoadDatabase "dbd/Spinnaker.dbd"
Spinnaker_registerRecordDeviceDriver pdbbase

## Load record instances
#dbLoadRecords("db/Spinnaker.db","user=dphan")

cd "${TOP}/iocBoot/${IOC}"
iocInit

## Start any sequence programs
#seq sncxxx,"user=dphan"
