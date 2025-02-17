#!../../bin/linux-x86_64/randomGen

#- You may have to change randomGen to something else
#- everywhere it appears in this file

# < envPaths

epicsEnvSet("TOP", "../..")
epicsEnvSet("IOC", "iocrandomGen")

cd "${TOP}"

## Register all support components
dbLoadDatabase "dbd/randomGen.dbd"
randomGen_registerRecordDeviceDriver pdbbase

## Load record instances
# dbLoadTemplate "db/user.substitutions"
dbLoadRecords "db/randomGen.db", "user=reinier"
# dbLoadRecords "db/dbSubExample.db", "user=reinier"

#- Set this to see messages from mySub
#-var mySubDebug 1

#- Run this to trace the stages of iocInit
#-traceIocInit

cd "${TOP}/iocBoot/${IOC}"
iocInit

## Start any sequence programs
#seq sncExample, "user=reinier"
