#!../../bin/linux-x86_64/PS3000A

dbLoadDatabase("../../dbd/PS3000A.dbd")
PS3000A_registerRecordDeviceDriver(pdbbase)

# Turn on asynTraceFlow and asynTraceError for global trace, i.e. no connected asynUser.
#asynSetTraceMask("", 0, 17)

PS3000AConfigure("ps3000a_port", 1000)

dbLoadRecords("../../db/PS3000A.db","P=TEST:,R=scope1:,PORT=ps3000a_port,ADDR=0,TIMEOUT=1,NPOINTS=1000")
dbLoadRecords("../../db/PS3000A_ch.db","P=TEST:,R=scope1:,PORT=ps3000a_port,ADDR=0,TIMEOUT=1,NPOINTS=1000")
dbLoadRecords("../../db/asynRecord.db","P=TEST:,R=asyn1,PORT=ps3000a_port,ADDR=0,OMAX=80,IMAX=80")
#asynSetTraceMask("ps3000a_port",0,0xff)
asynSetTraceIOMask("ps3000a_port",0,0x2)
iocInit()
