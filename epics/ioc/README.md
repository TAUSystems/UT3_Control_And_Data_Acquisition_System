EPICS driver and IOC for the PicoScope 3000 Series, based on the asynPortDriver (asyn), and pico_2000 EPICS driver (https://git.gsi.de/r3b_public/epics/pico_2000)

# Requirements
---

It is required to set the environment variable 'PICO_SDK' to point to the
installation path of the PICO SDK (including header files and libraries).

- libps3000a
- EPICS base
- asyn driver

# GUI
---

Included for MEDM in picoApp/adl.
Use the start_gui.sh script.


# How to
---
- Write your own `configure/RELEASE.local` to define your `$EPICS_BASE`, `$SUPPORT`, and `ASYN` paths.

My `.local` looks like this:
```
EPICS_BASE=/home/dphan/Applications/EPICS/epics-base
SUPPORT=/home/dphan/Applications/EPICS/support
ASYN=$(SUPPORT)/asyn-R4-44-2
```

- Define `PICO_SDK` path. On Linux, use `export PICO_SDK=/opt/picoscope`
- Rebuild
