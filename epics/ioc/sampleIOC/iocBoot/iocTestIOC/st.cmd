#!../../bin/linux-x86_64/TestIOC

#- You may have to change TestIOC to something else
#- everywhere it appears in this file

< envPaths

cd "${TOP}"

## Register all support components
dbLoadDatabase "dbd/TestIOC.dbd"
TestIOC_registerRecordDeviceDriver pdbbase

## Load record instances
#dbLoadRecords("db/TestIOC.db","user=dphan")

cd "${TOP}/iocBoot/${IOC}"
iocInit

## Start any sequence programs
#seq sncxxx,"user=dphan"
