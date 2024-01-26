from __future__ import annotations
from typing import TYPE_CHECKING

import os

import requests
from utils.redis import get_redis_client

from utils.types import ImageAnalysisFinishedMessage

IMAGE_PVS = [
    "device1/image",
    "device2/image",
]

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

def send_to_image_backend(value: P4PValue):
    requests.post(IMAGE_BACKEND_ENDPOINT_URL, data={'device_name': value.device_name, 'shot_id': value.shot_id},
                  files={'image_data': value.image_data},
                 )

def subscribe_to_PVs_for_upload():
    for image_pv in IMAGE_PVS:
        p4p_context.monitor(image_pv, send_to_image_backend)

def listen_for_and_process_analysis_complete_messages():
    redis_client = get_redis_client()
    ps = redis_client.pubsub()
    ps.subscribe('image_analysis_finished_ch')

    while True:
        message: ImageAnalysisFinishedMessage = ps.get_message()

        try:
            pv_name = last_analyzed_pv_from_device_name[message['device_name']]
        except KeyError:
            continue

        p4p_context.set(pv_name, message['shot_id'])


if __name__ == '__main__':
    subscribe_to_PVs_for_upload()
    listen_for_and_process_analysis_complete_messages()

