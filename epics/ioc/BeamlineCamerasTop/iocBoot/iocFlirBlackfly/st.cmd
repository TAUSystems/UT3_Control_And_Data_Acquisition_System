#!../../bin/linux-x86_64/FlirBlackfly

#- You may have to change FlirBlackfly to something else
#- everywhere it appears in this file

< envPaths

cd "${TOP}"

## Register all support components
dbLoadDatabase "dbd/FlirBlackfly.dbd"
FlirBlackfly_registerRecordDeviceDriver pdbbase

## Load record instances
#dbLoadRecords("db/FlirBlackfly.db","user=reinier")

cd "${TOP}/iocBoot/${IOC}"
iocInit

## Start any sequence programs
#seq sncxxx,"user=reinier"
