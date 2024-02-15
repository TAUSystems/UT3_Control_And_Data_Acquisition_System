epicsEnvSet("PORT_ESpecPointing", "Spectrometer:Pointing")

ADSpinnakerConfig($(PORT_ESpecPointing), "20057635")
asynSetTraceIOMask($(PORT_ESpecPointing), 0, 2)
dbLoadRecords("$(GENICAM_DB_FILE)", "P=$(PREFIX), R=$(PORT_ESpecPointing):, PORT=$(PORT_ESpecPointing)")

epicsEnvSet("PORT_PVA_ESpecPointing", "PVA_E_SPEC_Pointing")

NDPvaConfigure($(PORT_PVA_ESpecPointing), $(QSIZE), 0, $(PORT_ESpecPointing), 0, $(PREFIX)$(PORT_ESpecPointing):PVA:Image, 0, 0, 0)
dbLoadRecords("NDPva.template", "P=$(PREFIX), R=$(PORT_ESpecPointing):PVA:, PORT=$(PORT_PVA_ESpecPointing), ADDR=0, TIMEOUT=1, NDARRAY_PORT=$(PORT_ESpecPointing)")


