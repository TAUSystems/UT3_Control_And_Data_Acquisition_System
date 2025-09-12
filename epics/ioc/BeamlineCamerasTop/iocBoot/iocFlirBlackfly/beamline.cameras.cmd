< envPaths
errlogInit(20000)

dbLoadDatabase("$(TOP)/dbd/spinnakerApp.dbd")
spinnakerApp_registerRecordDeviceDriver(pdbbase) 

epicsEnvSet("GENICAM_DB_FILE", "$(TOP)/iocBoot/$(IOC)/FLIR_BFS-PGE-23S6M-C.template")

# From https://teams.microsoft.com/l/message/19:ecdae7d273e8403fa3fa8dfbc1f90793@thread.tacv2/1757710430866?tenantId=c424791c-0e81-45fb-a3d9-42fd987455ae&groupId=03cab077-56ed-4487-bf7c-4998d237c1f5&parentMessageId=1757109013200&teamName=UT3%20(External)&channelName=UT3%20SEET&createdTime=1757710430866
#####
# Pointing:
# -We're using the pointing camera from before behind divergence pinhole.
#  
# Spectral Dipole Input:
# -monitor the beam entering the first dipole
#  
# Spectral Dipole Output:
# -Low resolution roughly full energy spectrum monitor
#  
# Collimation Dipole Input:
# -High resolution, high energy spectrum monitor
#  
# Collimation Dipole Output:
# -should be nearly identical to the input profile.
# -verify the collimation and trajectory of the electron beam
# -Allow selection of electron energy with the Electron Energy Pinhole.
#  
# Target Monitor:
#-image DRZ/YAG at electron beam focal position to determine the effectiveness of the focusing.
#####


# Use this line for a specific camera by serial number, in this case a BlackFlyS GigE
epicsEnvSet("CAMERA_ID", "1234567")
# The port name for the detector
epicsEnvSet("PORT",   "PointingPort")
# Prefix for all records
epicsEnvSet("PREFIX", "Beamline:Pointing:")

< beamline.camera.cmd


epicsEnvSet("CAMERA_ID", "1234567")
epicsEnvSet("PORT",   "SpectralDipoleInputPort")
epicsEnvSet("PREFIX", "Beamline:SpectralDipole:Input:")
< beamline.camera.cmd

epicsEnvSet("CAMERA_ID", "1234567")
epicsEnvSet("PORT",   "SpectralDipoleOutputPort")
epicsEnvSet("PREFIX", "Beamline:SpectralDipole:Output:")
< beamline.camera.cmd

epicsEnvSet("CAMERA_ID", "1234567")
epicsEnvSet("PORT",   "CollimationDipoleInputPort")
epicsEnvSet("PREFIX", "Beamline:CollimationDipole:Input:")
< beamline.camera.cmd

epicsEnvSet("CAMERA_ID", "1234567")
epicsEnvSet("PORT",   "CollimationDipoleOutputPort")
epicsEnvSet("PREFIX", "Beamline:CollimationDipole:Output:")
< beamline.camera.cmd

epicsEnvSet("CAMERA_ID", "1234567")
epicsEnvSet("PORT",   "TargetMonitorPort")
epicsEnvSet("PREFIX", "Beamline:TargetMonitor:")
< beamline.camera.cmd

startPVAServer

set_requestfile_path("$(ADGENICAM)/GenICamApp/Db")
set_requestfile_path("$(ADSPINNAKER)/spinnakerApp/Db")

iocInit()

# save things every thirty seconds
create_monitor_set("auto_settings.req", 30,"P=$(PREFIX)")

# Wait for enum callbacks to complete
epicsThreadSleep(1.0)

# Wait for callbacks on the property limits (DRVL, DRVH) to complete
epicsThreadSleep(1.0)

