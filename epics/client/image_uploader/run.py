from __future__ import annotations
from typing import TYPE_CHECKING

import os
import json
from io import BytesIO
from functools import partial

import logging
logging.basicConfig(level=logging.INFO, force=True)

from numpy.typing import NDArray
from tifffile import imwrite as write_tiff

import requests
from utils.redis import get_redis_client
from utils.types import ImageAnalysisFinishedMessage, ImageDeviceDirectoryEntry

IMAGE_DEVICES = {
    'Spectrometer_LowEnergy': ImageDeviceDirectoryEntry("Electrons:Spectrometer_LowEnergy:ImageArrayData", "Electrons:Spectrometer_SpectrumPNG:LastAnalyzedShotID"),
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
    from p4p import Value as P4PValue

work_queue = WorkQueue(WORK_QUEUE_NUM_WORKERS)
p4p_context = P4PContext('pva', queue=work_queue)

def send_to_image_backend(device_name: str, image_data: NDArray):
    # get shot number
    shot_id = p4p_context.get("ShotIDPV")
    
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
        except KeyError, AttributeError:
            logging.warning(f"No LastAnalyzed PV for device {image_finished_message['device_name']}")
            continue

        p4p_context.put(last_analyzed_pv_name, image_finished_message['shot_id'])
        logging.info(f"Set PV {last_analyzed_pv_name} to '{image_finished_message['shotid']}'")

if __name__ == '__main__':
    subscribe_to_PVs_for_upload()
    listen_for_and_process_analysis_complete_messages()
