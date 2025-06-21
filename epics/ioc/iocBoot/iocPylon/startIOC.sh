#!/bin/bash

IOC_DIR="/root/linux-ioc/UT3_Control_And_Data_Acquisition_System/epics/ioc/iocBoot/iocPylon"
IOC_EXEC="/root/linux-ioc/UT3_Control_And_Data_Acquisition_System/epics/ioc/bin/linux-x86_64/pylonApp"
IOC_CMD="/root/linux-ioc/UT3_Control_And_Data_Acquisition_System/epics/ioc/iocBoot/iocPylon/st.cmd.ut3-laserdiag-ioc"
PORT=20000
LOGFILE="$IOC_DIR/laserdiag-ioc.log"

cd "$IOC_DIR"

# Ensure log file exists and is writable
touch "$LOGFILE"
chmod 664 "$LOGFILE"

# Start IOC with procServ
exec procServ --noautorestart --foreground --logfile "$LOGFILE" "$PORT" "$IOC_EXEC" "$IOC_CMD"

