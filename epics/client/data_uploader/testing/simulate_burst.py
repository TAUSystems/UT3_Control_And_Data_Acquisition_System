from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime, timezone
from time import sleep

from epics import caput
from epics.pv import PV

from data_uploader.utils.types import BurstStatus

pvs = {'session_title': PV("Tr")}

pvs: dict[str, PV] = {
    'burst_status': PV("Timing:TriggerGeneration:Status"),
    'burst_timestamp': PV("Timing:TriggerGeneration:BurstTimestamp"),
    'burst_frequency': PV("Timing:TriggerGeneration:Frequency_GET"),
    'burst_num_shots': PV("Timing:TriggerGeneration:NumShots"),

    'session_title': PV("Data:Scan:Session"),
    'scan_number': PV("Data:Scan:Number"),
    'scan_title': PV("Data:Scan:Title"),
}

def configure_cameras():
    stop_acquisition()
    for screen in ['Pointing', 'LowEnergy', 'HighEnergy']:
        caput(f"E:Spectrometer:{screen}:TriggerSource", "Software")

def start_acquisition():
    for screen in ['Pointing', 'LowEnergy', 'HighEnergy']:
        caput(f"E:Spectrometer:{screen}:Acquire", 1)

def stop_acquisition():
    for screen in ['Pointing', 'LowEnergy', 'HighEnergy']:
        caput(f"E:Spectrometer:{screen}:Acquire", 0)

def trigger_cameras():
    for screen in ['Pointing', 'LowEnergy', 'HighEnergy']:
        caput(f"E:Spectrometer:{screen}:TriggerSoftware.PROC", 1)


def main(num_shots: int, frequency: float):

    burst_status = BurstStatus(pvs['burst_status'].get())
    if burst_status != BurstStatus.Idle:
        raise ValueError(f"Not ready to create burst! Status is {BurstStatus(burst_status)}")

    if not (0.01 < frequency < 50.0):
        raise ValueError("Frequency should be between 0.01 and 50.0 Hz")

    configure_cameras()

    pvs['session_title'].put(f"Simulate burst {datetime.now(tz=timezone.utc):%Y-%m-%dT%H:%M:%SZ}", wait=True)
    pvs['scan_number'].put(1)
    pvs['scan_title'].put(f"Simulate burst: {num_shots} shots at {frequency:.1f} Hz", wait=True)
    pvs['burst_num_shots'].put(num_shots, wait=True)
    pvs['burst_frequency'].put(frequency, wait=True)

    pvs['burst_status'].put(BurstStatus.Preparing.name)
    sleep(0.1)

    for shot_number in range(num_shots):
        trigger_cameras()
        sleep(1 / frequency)

    pvs['burst_status'].put(BurstStatus.Idle.name)

if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument("--num_shots", '-n',
        type=int,
        default=1,
        help="Number of shots",
    )
    ap.add_argument("--frequency", '-f',
        type=float,
        default=1.0,
        help="Repetition rate in Hz",
    )
    
    args = ap.parse_args()

    main(args.num_shots, args.frequency)
