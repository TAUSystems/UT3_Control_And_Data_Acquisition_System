#!../../bin/linux-x86_64/newport

#- You may have to change newport to something else
#- everywhere it appears in this file

< envPaths

## Register all support components
dbLoadDatabase "$(TOP)/dbd/newport.dbd"
newport_registerRecordDeviceDriver pdbbase

### Motors
dbLoadTemplate "vertical.newportconexpp.substitutions"

drvAsynSerialPortConfigure("DivergencePinholeVPort", "/dev/ttyUSB0", 0, 0, 0)
asynOctetSetInputEos("DivergencePinholeVPort",0,"\r\n")
asynOctetSetOutputEos("DivergencePinholeVPort",0,"\r\n")
asynSetOption("DivergencePinholeVPort",0,"baud","115200")
asynSetOption("DivergencePinholeVPort",0,"bits","8")
asynSetOption("DivergencePinholeVPort",0,"stop","1")
asynSetOption("DivergencePinholeVPort",0,"parity","none")
asynSetOption("DivergencePinholeVPort",0,"clocal","Y")
asynSetOption("DivergencePinholeVPort",0,"crtscts","N")

asynSetTraceIOMask("DivergencePinholeVPort", 0, 2)
#asynSetTraceMask("DivergencePinholeVPort", 0, 9)

# Load asyn record
dbLoadRecords("$(ASYN)/db/asynRecord.db", "P=IOC:,R=DivergencePinholeVPort,PORT=DivergencePinholeVPort, ADDR=0,OMAX=256,IMAX=256")

# AG_CONEXCreateController(asyn port, serial port, controllerID, 
#                          active poll period (ms), idle poll period (ms)) 
AG_CONEXCreateController("DivergencePinholeVCtlr", "DivergencePinholeVPort", 1, 50, 500)
asynSetTraceIOMask("DivergencePinholeVCtlr", 0, 2)
#asynSetTraceMask("DivergencePinholeVCtlr", 0, 255)

AG_CONEXCreateController("EnergyPinholeVCtlr", "DivergencePinholeVPort", 2, 50, 500)
asynSetTraceIOMask("EnergyPinholeVCtlr", 0, 2)
#asynSetTraceMask("EnergyPinholeVCtlr", 0, 255)

#AG_CONEXCreateController("EnergyPinholeVCtlr", "EnergyPinholeVPort", 1, 50, 500)
#asynSetTraceIOMask("EnergyPinholeVCtlr", 0, 2)
##asynSetTraceMask("EnergyPinholeVCtlr", 0, 255)

cd "${TOP}/iocBoot/${IOC}"
iocInit

dbpf IOC:m1.RTRY 0
dbpf IOC:m1.NTM 0