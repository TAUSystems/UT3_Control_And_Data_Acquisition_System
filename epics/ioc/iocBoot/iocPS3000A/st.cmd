#!../../bin/linux-x86_64/PS3000A

< envPaths

dbLoadDatabase("../../dbd/PS3000A.dbd")
PS3000A_registerRecordDeviceDriver(pdbbase)

# Turn on asynTraceFlow and asynTraceError for global trace, i.e. no connected asynUser.
#asynSetTraceMask("", 0, 17)

PS3000AConfigure("ps3000a_port", 1000)

epicsEnvSet(P, "E:")
epicsEnvSet(R, "ICT:")
epicsEnvSet(PORT, "ps3000a_port")

dbLoadRecords("../../db/PS3000A.db","P=$(P),R=$(R),PORT=$(PORT),ADDR=0,TIMEOUT=1,NPOINTS=1000")
dbLoadRecords("../../db/ict.db","P=$(P),R=$(R),C=B,NPOINTS=1000")
dbLoadRecords("../../db/asynRecord.db","P=$(P),R=ps3000a_asyn,PORT=$(PORT),ADDR=0,OMAX=80,IMAX=80")

#asynSetTraceMask("$(PORT)",0,0xff)
asynSetTraceIOMask("$(PORT)",0,0x2)
iocInit()

dbpf $(P)$(R)PicoConnect 1
dbpf $(P)$(R)Run 1
