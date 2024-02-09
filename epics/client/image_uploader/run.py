from __future__ import annotations
from typing import TYPE_CHECKING

import os
import json
from io import BytesIO
from functools import partial
from datetime import datetime, timezone, timedelta

import logging
logging.basicConfig(level=logging.INFO, force=True)

from tifffile import imwrite as write_tiff

import requests
from utils.redis import get_redis_client
from utils.types import ImageAnalysisFinishedMessage, ImageDeviceDirectoryEntry

IMAGE_DEVICES = {
    'Electron:Spectrometer:LowEnergy': ImageDeviceDirectoryEntry(
        "Electrons:Spectrometer:LowEnergy:PVA:Image", 
        "Electrons:Spectrometer:LowEnergy:PVA:ArrayCounter_RBV", 
        "Electrons:Spectrometer:LastAnalyzedShotID"
    ),
    'Electron:Spectrometer:HighEnergy': ImageDeviceDirectoryEntry(
        "Electrons:Spectrometer:HighEnergy:PVA:Image", 
        "Electrons:Spectrometer:HighEnergy:PVA:ArrayCounter_RBV", 
        None
    ),
    'Electron:Spectrometer:Pointing': ImageDeviceDirectoryEntry(
        "Electrons:Spectrometer:Pointing:PVA:Image", 
        "Electrons:Spectrometer:Pointing:PVA:ArrayCounter_RBV", 
        None
    ),
}

WORK_QUEUE_NUM_WORKERS = 12
IMAGE_BACKEND_ENDPOINT_URL = "http://localhost:5000"

# the PV whose value to set to shot ID given an image_analysis_finished message 
# device_name field
last_analyzed_pv_from_device_name = {
    'Spectrometer_LowEnergy': "Electrons:Spectrometer_SpectrumPNG:LastAnalyzedShotID",
    'eScreenA': "Electrons:Spectrometer_SpectrumPNG:LastAnalyzedShotID",
}

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

    # fire POST request
    requests.post(IMAGE_BACKEND_ENDPOINT_URL, 
                    data={'device_name': device_name, 'shot_id': shot_id},
                    files={'image_data': tiff_bytes},
                 )

def subscribe_to_PVs_for_upload():
    for device_name, device_directory_entry in IMAGE_DEVICES.items():
        p4p_context.monitor(device_directory_entry.image_pv_name, partial(send_to_image_backend, device_name))

def listen_for_and_process_analysis_complete_messages():
    redis_client = get_redis_client()
    ps = redis_client.pubsub()
    ps.subscribe('image_analysis_finished_ch')

    while True:
        message: ImageAnalysisFinishedMessage = ps.get_message(ignore_subscribe_messages=True, timeout=None)

        if message is None:
            continue

        image_finished_message = json.loads(message['data'])
	
        try:
            last_analyzed_pv_name = IMAGE_DEVICES[image_finished_message['device_name']].last_analyzed_pv_name
        except (KeyError, AttributeError):
            logging.warning(f"No LastAnalyzed PV for device {image_finished_message['device_name']}")
            continue

        if last_analyzed_pv_name is not None:
            p4p_context.put(last_analyzed_pv_name, image_finished_message['shot_id'])
            logging.info(f"Set PV {last_analyzed_pv_name} to '{image_finished_message['shotid']}'")

if __name__ == '__main__':
    subscribe_to_PVs_for_upload()
    listen_for_and_process_analysis_complete_messages()
