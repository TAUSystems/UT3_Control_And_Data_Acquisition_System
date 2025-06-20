#!/bin/bash

IOC_DIR="/root/linux-ioc/UT3_Control_And_Data_Acquisition_System/epics/ioc/iocBoot/iocFLIRCamera"
IOC_EXEC="/root/linux-ioc/UT3_Control_And_Data_Acquisition_System/epics/ioc/bin/linux-x86_64/spinnakerApp"
IOC_CMD="/root/linux-ioc/UT3_Control_And_Data_Acquisition_System/epics/ioc/iocBoot/iocFLIRCamera/st.cmd.ut3-linux-ioc"
PORT=20000
LOGFILE="$IOC_DIR/espec-ioc.log"

cd "$IOC_DIR"

# Ensure log file exists and is writable
touch "$LOGFILE"
chmod 664 "$LOGFILE"

# Start IOC with procServ
exec procServ --noautorestart --foreground --logfile "$LOGFILE" "$PORT" "$IOC_EXEC" "$IOC_CMD"

