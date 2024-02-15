epicsEnvSet("PORT_ESpecHE", "Spectrometer:HighEnergy")

ADSpinnakerConfig($(PORT_ESpecHE), "20125390")
asynSetTraceIOMask($(PORT_ESpecHE), 0, 2)
dbLoadRecords("$(GENICAM_DB_FILE)", "P=$(PREFIX), R=$(PORT_ESpecHE):, PORT=$(PORT_ESpecHE)")

epicsEnvSet("PORT_PVA_ESpecHE", "PVA_E_SPEC_HE")

NDPvaConfigure($(PORT_PVA_ESpecHE), $(QSIZE), 0, $(PORT_ESpecHE), 0, $(PREFIX)$(PORT_ESpecHE):PVA:Image, 0, 0, 0)
dbLoadRecords("NDPva.template", "P=$(PREFIX), R=$(PORT_ESpecHE):PVA:, PORT=$(PORT_PVA_ESpecHE), ADDR=0, TIMEOUT=1, NDARRAY_PORT=$(PORT_ESpecHE)")


