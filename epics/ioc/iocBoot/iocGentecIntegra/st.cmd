#!../../bin/linux-x86_64/GentecIntegra

#- You may have to change GentecIntegra to something else
#- everywhere it appears in this file

< envPaths

cd "${TOP}"

## Register all support components
dbLoadDatabase "dbd/GentecIntegra.dbd"
GentecIntegra_registerRecordDeviceDriver pdbbase

## Load record instances
#dbLoadRecords("db/GentecIntegra.db","user=reinier")

cd "${TOP}/iocBoot/${IOC}"
iocInit

## Start any sequence programs
#seq sncxxx,"user=reinier"
