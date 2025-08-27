#!../../bin/linux-x86_64/zaberMotion

< envPaths

## Register all support components
dbLoadDatabase "$(TOP)/dbd/zaberMotion.dbd"
zaberMotion_registerRecordDeviceDriver pdbbase

## motorUtil (allstop & alldone)
dbLoadRecords("$(MOTOR)/db/motorUtil.db", "P=zaberMotion:")

###
# ZaberMotionSetDbPath(
#    path of local copy of zaber device database
# )
###
ZaberMotionSetDbPath("/home/ubuntu/Downloads/devices-public.sqlite")

###
# ZaberMotionCreateController(
#    asyn motor port (will be created),
#    num axes,
#    moving poll period (ms),
#    idle poll period (ms)
#    address or serial port name of zaber device (prefixed with tcp:// or serial://)
#    zaber device number (1-indexed)
# )
###
ZaberMotionCreateController("DivergencePinholePort",  1, 100, 5000, "serial:///dev/ttyUSB0", 0)
ZaberMotionCreateController("EnergyPinholePort",      1, 100, 5000, "serial:///dev/ttyUSB1", 0)

cd "${TOP}/iocBoot/${IOC}"
dbLoadTemplate("horizontal.zaber.substitutions")

iocInit

## motorUtil (allstop & alldone)
motorUtilInit("zaberMotion:")

# Boot complete
