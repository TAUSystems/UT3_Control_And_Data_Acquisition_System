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

# List of PVs

Most common used
```
TEST:scope1:PicoConnect    -- 0 to disconnect, 1 to connect
TEST:scope1:PicoConnected  -- check connection to PicoScope
TEST:scope1:Enabled_A      -- 0 to disable, 1 to enable channel A
TEST:scope1:Enabled_B      -- 0 to disable, 1 to enable channel A
TEST:scope1:TriggerSource  -- set trigger source, 0 to channel A, 1 to channel B
TEST:scope1:SampleLength   -- number of sampling points
TEST:scope1:VoltOffset_A   -- voltage offset channel A, in mV
TEST:scope1:VoltOffset_B   -- voltage offset channel A, in mV
TEST:scope1:ChannelARange  -- range enum, 0 [-20mV, 20mV], 1 [-50mV, 50mV], please see ps3000aApi.h for more
TEST:scope1:ChannelBRange  -- range enum, 0 [-20mV, 20mV], 1 [-50mV, 50mV], please see ps3000aApi.h for more
TEST:scope1:Run            -- run task command
TEST:scope1:Waveform_A_RBV -- channel A waveform array
TEST:scope1:Waveform_B_RBV -- channel B waveform array
```


All PVs:
```
TEST:scope1:FullTime_RBV
TEST:scope1:TimePerDiv_RBV
TEST:scope1:SigGenPkToPk_RBV
TEST:scope1:SigGenOffset_RBV
TEST:scope1:DownsampledFrequency_RBV
TEST:scope1:SampleFrequency_RBV
TEST:scope1:SampleLength_RBV
TEST:scope1:DownSampleRatio_RBV
TEST:scope1:SigGenFrequency_RBV
TEST:scope1:TriggerDelay_RBV
TEST:scope1:NoiseAmplitude_RBV
TEST:scope1:UpdateTime_RBV
TEST:scope1:MinValue_RBV
TEST:scope1:ScopeClear
TEST:scope1:MaxValue_RBV
TEST:scope1:MeanValue_RBV
TEST:scope1:VoltsPerDiv_A_RBV
TEST:scope1:VoltOffset_A_RBV
TEST:scope1:ChannelAThreshold_RBV
TEST:scope1:VoltsPerDiv_B_RBV
TEST:scope1:VoltOffset_B_RBV
TEST:scope1:ChannelBThreshold_RBV
TEST:scope1:VoltsPerDiv_C_RBV
TEST:scope1:VoltOffset_C_RBV
TEST:scope1:ChannelCThreshold_RBV
TEST:scope1:VoltsPerDiv_D_RBV
TEST:scope1:VoltOffset_D_RBV
TEST:scope1:ChannelDThreshold_RBV
TEST:scope1:SigGenPkToPk
TEST:scope1:SigGenOffset
TEST:scope1:DownsampledFrequency
TEST:scope1:SampleFrequency
TEST:scope1:SampleLength
TEST:scope1:DownSampleRatio
TEST:scope1:SigGenFrequency
TEST:scope1:TriggerDelay
TEST:scope1:NoiseAmplitude
TEST:scope1:UpdateTime
TEST:scope1:VoltOffset_A
TEST:scope1:ChannelAThreshold
TEST:scope1:VoltOffset_B
TEST:scope1:ChannelBThreshold
TEST:scope1:VoltOffset_C
TEST:scope1:ChannelCThreshold
TEST:scope1:VoltOffset_D
TEST:scope1:ChannelDThreshold
TEST:asyn1
TEST:scope1:Run_RBV
TEST:scope1:PicoConnected_RBV
TEST:scope1:PicoConnect_RBV
TEST:scope1:Enabled_A_RBV
TEST:scope1:Enabled_B_RBV
TEST:scope1:Enabled_C_RBV
TEST:scope1:Enabled_D_RBV
TEST:scope1:Run
TEST:scope1:PicoConnect
TEST:scope1:Enabled_A
TEST:scope1:Enabled_B
TEST:scope1:Enabled_C
TEST:scope1:Enabled_D
TEST:scope1:MaxPoints_RBV
TEST:scope1:PicoStatus
TEST:scope1:TimeBaseHopr
TEST:scope1:TimeBaseLopr
TEST:scope1:TimeBaseNelm
TEST:scope1:SigGenWaveType_RBV
TEST:scope1:TriggerSource_RBV
TEST:scope1:VoltsPerDivSelect_A_RBV
TEST:scope1:ChannelARange_RBV
TEST:scope1:VoltsPerDivSelect_B_RBV
TEST:scope1:ChannelBRange_RBV
TEST:scope1:VoltsPerDivSelect_C_RBV
TEST:scope1:ChannelCRange_RBV
TEST:scope1:VoltsPerDivSelect_D_RBV
TEST:scope1:ChannelDRange_RBV
TEST:scope1:TimePerDivSelect
TEST:scope1:SigGenWaveType
TEST:scope1:TriggerSource
TEST:scope1:VoltsPerDivSelect_A
TEST:scope1:ChannelARange
TEST:scope1:VoltsPerDivSelect_B
TEST:scope1:ChannelBRange
TEST:scope1:VoltsPerDivSelect_C
TEST:scope1:ChannelCRange
TEST:scope1:VoltsPerDivSelect_D
TEST:scope1:ChannelDRange
TEST:scope1:TimeBase_RBV
TEST:scope1:Waveform_A_RBV
TEST:scope1:Waveform_B_RBV
TEST:scope1:Waveform_C_RBV
TEST:scope1:Waveform_D_RBV
```
