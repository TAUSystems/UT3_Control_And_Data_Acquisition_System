from __future__ import annotations
from typing import TYPE_CHECKING

import json

import logging
logging.basicConfig(level=logging.INFO, force=True)

from dotenv import dotenv_values
env = dotenv_values()

from utils.redis import get_redis_client
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

def listen_for_and_process_analysis_complete_messages():
    redis_client = get_redis_client()
    ps = redis_client.pubsub()
    ps.subscribe('image_analysis_complete_ch')

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
    listen_for_and_process_analysis_complete_messages()
