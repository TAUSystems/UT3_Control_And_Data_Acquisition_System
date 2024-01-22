#!../../bin/linux-x86_64/TestIOC

#- You may have to change TestIOC to something else
#- everywhere it appears in this file

< envPaths

cd "${TOP}"

## Register all support components
dbLoadDatabase "dbd/TestIOC.dbd"
TestIOC_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadTemplate "db/user.substitutions"
dbLoadRecords "db/TestIOCVersion.db", "user=dphan"
dbLoadRecords "db/dbSubExample.db", "user=dphan"

#- Set this to see messages from mySub
#-var mySubDebug 1

#- Run this to trace the stages of iocInit
#-traceIocInit

cd "${TOP}/iocBoot/${IOC}"
iocInit

## Start any sequence programs
#seq sncExample, "user=dphan"
