epicsEnvSet("PORT_TestCamera", "TestCamera")

ADSpinnakerConfig($(PORT_TestCamera), "23228393")
asynSetTraceIOMask($(PORT_TestCamera), 0, 2)
dbLoadRecords("$(GENICAM_DB_FILE)", "P=$(PREFIX), R=$(PORT_TestCamera):, PORT=$(PORT_TestCamera)")

epicsEnvSet("PORT_PVA_TestCamera", "PVA_E_SPEC_Pointing")

NDPvaConfigure($(PORT_PVA_TestCamera), $(QSIZE), 0, $(PORT_TestCamera), 0, $(PREFIX)$(PORT_TestCamera):PVA:Image, 0, 0, 0)
dbLoadRecords("NDPva.template", "P=$(PREFIX), R=$(PORT_TestCamera):PVA:, PORT=$(PORT_PVA_TestCamera), ADDR=0, TIMEOUT=1, NDARRAY_PORT=$(PORT_TestCamera)")


