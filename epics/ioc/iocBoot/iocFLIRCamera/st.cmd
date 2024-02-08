#!../../bin/linux-x86_64/spinnaker

#- You may have to change spinnaker to something else
#- everywhere it appears in this file

< envPaths

cd "${TOP}"

## Register all support components
dbLoadDatabase "dbd/spinnaker.dbd"
spinnaker_registerRecordDeviceDriver pdbbase

## Load record instances
#dbLoadRecords("db/spinnaker.db","user=dphan")

cd "${TOP}/iocBoot/${IOC}"
iocInit

## Start any sequence programs
#seq sncxxx,"user=dphan"
