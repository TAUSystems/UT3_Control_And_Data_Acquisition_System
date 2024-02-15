epicsEnvSet("PORT_ESpecLE", "Spectrometer:LowEnergy")

ADSpinnakerConfig($(PORT_ESpecLE), "20541743")
asynSetTraceIOMask($(PORT_ESpecLE), 0, 2)
dbLoadRecords("$(GENICAM_DB_FILE)", "P=$(PREFIX), R=$(PORT_ESpecLE):, PORT=$(PORT_ESpecLE)")

epicsEnvSet("PORT_PVA_ESpecLE", "PVA_E_SPEC_LE")

NDPvaConfigure($(PORT_PVA_ESpecLE), $(QSIZE), 0, $(PORT_ESpecLE), 0, $(PREFIX)$(PORT_ESpecLE):PVA:Image, 0, 0, 0)
dbLoadRecords("NDPva.template", "P=$(PREFIX), R=$(PORT_ESpecLE):PVA:, PORT=$(PORT_PVA_ESpecLE), ADDR=0, TIMEOUT=1, NDARRAY_PORT=$(PORT_ESpecLE)")


