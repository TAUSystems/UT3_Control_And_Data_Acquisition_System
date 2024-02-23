from __future__ import annotations
from typing import TYPE_CHECKING

from io import BytesIO
from functools import partial
from datetime import datetime, timezone, timedelta
from time import sleep
from os import environ as env

import logging
logging.basicConfig(level=logging.INFO, force=True)

from tifffile import imwrite as write_tiff

import requests
from utils.types import ImageAnalysisFinishedMessage, ImageDeviceDirectoryEntry

# TODO: replace by config file
IMAGE_DEVICES = {
    'E:Spectrometer:LowEnergy': ImageDeviceDirectoryEntry(
        "E:Pva:Spectrometer:LowEnergy:Image", 
        "E:Pva:Spectrometer:LowEnergy:ArrayCounter_RBV", 
        "E:Spectrometer:LastAnalyzedShotID"
    ),
    'E:Spectrometer:HighEnergy': ImageDeviceDirectoryEntry(
        "E:Pva:Spectrometer:HighEnergy:Image", 
        "E:Pva:Spectrometer:HighEnergy:ArrayCounter_RBV", 
        None
    ),
    'E:Spectrometer:Pointing': ImageDeviceDirectoryEntry(
        "E:Pva:Spectrometer:Pointing:Image", 
        "E:Pva:Spectrometer:Pointing:ArrayCounter_RBV", 
        None
    ),
}

WORK_QUEUE_NUM_WORKERS = 12

from p4p.client.thread import Context as P4PContext
from p4p.rpc import WorkQueue

if TYPE_CHECKING:
    from p4p.nt import NTNDArray

work_queue = WorkQueue(WORK_QUEUE_NUM_WORKERS)
p4p_context = P4PContext('pva', queue=work_queue)

def send_to_image_backend(device_name: str, image_data: NTNDArray):
    # get shot number
    burst_timestamp_ms, frequency_Hz, shot_index = p4p_context.get(["Timing:TriggerGeneration:BurstTimestamp", 
                                                                    "Timing:TriggerGeneration:Frequency", 
                                                                    IMAGE_DEVICES[device_name].array_counter_pv_name,
                                                                  ])
    burst_datetime = datetime.fromtimestamp(burst_timestamp_ms / 1e3, timezone.utc)
    shot_datetime = burst_datetime + timedelta(seconds=shot_index / frequency_Hz)

    shot_id = f"burst-{burst_datetime:%Y-%m-%dT%H-%M-%S-%fZ}/shot-{shot_datetime:%Y-%m-%dT%H-%M-%S-%fZ}"

    # convert NDArray to tiff file byte array
    tiff_bytes = BytesIO()    
    write_tiff(tiff_bytes, image_data)
    tiff_bytes.seek(0)

    # fire POST request
    response = requests.post(env['IMAGE_BACKEND_ENDPOINT_URL'], 
                             data={'device_name': device_name, 'shot_id': shot_id},
                             files={'image_data': tiff_bytes},
                            )

    response_data = response.json()

    if ('message' not in response_data) or (response_data['message'] != "received image data"):
        logging.error(f"Failed to post image data for {shot_id} / {device_name}: {response_data}")
    
    else:
        logging.info(f"Posted image data for {shot_id} / {device_name}")


def subscribe_to_PVs_for_upload():
    for device_name, device_directory_entry in IMAGE_DEVICES.items():
        p4p_context.monitor(device_directory_entry.image_pv_name, partial(send_to_image_backend, device_name))
        logging.info(f"Monitoring {device_directory_entry.image_pv_name}.")

if __name__ == '__main__':
    subscribe_to_PVs_for_upload()
    while True:
        sleep(1e9)
