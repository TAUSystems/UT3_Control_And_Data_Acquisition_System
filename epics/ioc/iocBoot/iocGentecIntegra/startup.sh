#!/bin/bash

IOC_DIR="/root/UT3_Control_And_Data_Acquisition_System/epics/ioc/iocBoot/iocGentecIntegra"
IOC_EXEC="/root/UT3_Control_And_Data_Acquisition_System/epics/ioc/bin/linux-x86_64/GentecIntegra"
IOC_CMD="/root/UT3_Control_And_Data_Acquisition_System/epics/ioc/iocBoot/iocGentecIntegra/st.cmd"
PORT=20000
LOGFILE="$IOC_DIR/ioc-gentecintegra.log"

cd "$IOC_DIR"

# Ensure log file exists and is writable
touch "$LOGFILE"
chmod 664 "$LOGFILE"

# Start IOC binary with st.cmd using procServ
exec procServ\
	        --noautorestart \
		--foreground \
		--logfile "$LOGFILE" \
		"$PORT" \
		"$IOC_EXEC" "$IOC_CMD"
