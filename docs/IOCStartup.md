To run the IOCs, the EPICS base and synApps support need to be built. See [Installation](docs/Installation.md) on how to build those systems.

# Camera IOC

```bash
cd $EPICS_PATH/ioc
```

Modify the `$(SUPPORT)` and `$(EPICS_BASE)` paths in `configure/RELEASE` to match your local EPICS installation setup. Run `make` to build the IOC applications and the IOC boot.

To run the camera IOC

```bash
cd $EPICS_PATH/ioc/iocBoot/iocFLIRCamera
../../bin/linux-x86_64/delaygenApp ./st.cmd.ut3-electron-spectrometer
```

## Phoebus GUI for the cameras


