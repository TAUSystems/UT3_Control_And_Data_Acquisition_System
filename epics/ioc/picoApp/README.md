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

AUTOSAVE = $(SUPPORT)/autosave-R5-11
ASYN = $(SUPPORT)/asyn-R4-44-2
BUSY = $(SUPPORT)/busy-R1-7-4
CALC = $(SUPPORT)/calc-R3-7-5
SSCAN = $(SUPPORT)/sscan-R2-11-6
STD = $(SUPPORT)/std-R3-6-4
STREAMDEVICE = $(SUPPORT)/StreamDevice-2-8-24

AREA_DETECTOR = $(SUPPORT)/areaDetector-R3-13 <-- This might need to change depending on which version of AD installed
ADCORE = $(AREA_DETECTOR)/ADCore
ADAPP = $(ADCORE)/ADApp
ADSUPPORT = $(AREA_DETECTOR)/ADSupport
ADSIMDETECTOR = $(AREA_DETECTOR)/ADSimDetector
ADSIMDETECTOR_APP = $(ADSIMDETECTOR)/simDetectorApp
ADGENICAM = $(AREA_DETECTOR)/ADGenICam
ADSPINNAKER = $(AREA_DETECTOR)/ADSpinnaker
ADSPINNAKER_APP = $(ADSPINNAKER)/spinnakerApp
ADSPINNAKER_SUPPORT = $(ADSPINNAKER)/spinnakerSupport
```

- Define `PICO_SDK` path. On Linux, use `export PICO_SDK=/opt/picoscope`
- Rebuild

## To setup the PS3000A IOC:
- Connect the HW on an USB3.2 port on the IOC's host.
- Build the IOC.
- Run `st.cmd`.
- Most of the setting has been correctly set within `ConnectPicoScope()` function call. Users just need to set the following PVs:
```
TEST:scope1:PicoConnect 1
TEST:scope1:SampleLength 1000
TEST:scope1:Run 1
```
- Return waveforms are voltages values in unit of microVolts.


# List of PVs

Most common used
```
TEST:scope1:PicoConnect 1      <-- Connect to HW
TEST:scope1:ChannelARange 8    <-- Set A range to [-10 V, 10 V]
TEST:scope1:ChannelBRange 1    <-- Set B range to [-50mV, 50mV]
TEST:scope1:Run 1              <-- Start data acquisition
TEST:scope1:Waveform_A_RBV     <-- Obtain waveform A
TEST:scope1:Waveform_B_RBV     <-- Obtain waveform B
TEST:scope1:Run 0              <-- Stop data acquisition
TEST:scope1:PicoConnect 0      <-- Disconnect to HW
```

Range encode values:
- 0: [ -20mV,  20mV]
- 1: [ -50mV,  50mV]
- 2: [-100mV, 100mV]
- 3: [-200mV, 200mV]
- 4: [-500mV, 500mV]
- 5: [   -1V,    1V]
- 6: [   -2V,    2V]
- 7: [   -5V,    5V]
- 8: [  -10V,   10V]
- 9: [  -20V,   20V]


All PVs (mostly read-only)
```
TEST:scope1:SampleFrequency_RBV
TEST:scope1:SampleLength_RBV
TEST:asyn1
TEST:scope1:Run_RBV
TEST:scope1:PicoConnected_RBV
TEST:scope1:PicoConnect_RBV
TEST:scope1:Run
TEST:scope1:PicoConnect
TEST:scope1:MaxPoints_RBV
TEST:scope1:TriggerSource_RBV
TEST:scope1:ChannelARange_RBV
TEST:scope1:ChannelBRange_RBV
TEST:scope1:ChannelARange
TEST:scope1:ChannelBRange
TEST:scope1:TimeBase_RBV
TEST:scope1:Waveform_A_RBV
TEST:scope1:Waveform_B_RBV
```
