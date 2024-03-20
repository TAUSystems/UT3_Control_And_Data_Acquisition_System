from __future__ import annotations
from typing import TYPE_CHECKING

import json

# TODO: logging config file
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", force=True)

from image_analysis_complete_handler.utils.env import get_env
from image_analysis_complete_handler.utils.redis import get_redis_client
from image_analysis_complete_handler.utils.types import ImageAnalysisCompleteData, ImageDeviceDirectoryEntry
from image_analysis_complete_handler.handlers.last_analyzed_shotid_pv import PopulateLastAnalyzedShotIDPV
from image_analysis_complete_handler.handlers.analysis_folder_links import CreateAnalysisFolderLinks
if TYPE_CHECKING:
    from image_analysis_complete_handler.handlers.base import ImageAnalysisCompleteHandler


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

work_queue = WorkQueue(WORK_QUEUE_NUM_WORKERS)
p4p_context = P4PContext('pva') #, queue=work_queue)

# Set up message handlers
last_analyzed_shot_pvs = {device_name: device_pv_names.last_analyzed_pv_name 
                          for device_name, device_pv_names in IMAGE_DEVICES.items()
                          if device_pv_names.last_analyzed_pv_name
                         }
env = get_env()
handlers: list[ImageAnalysisCompleteHandler] = [
    PopulateLastAnalyzedShotIDPV(last_analyzed_shot_pvs),
    CreateAnalysisFolderLinks(env.get('DATA_DISK_STORAGE_BASE_DIRECTORY')),
]

def listen_for_and_process_analysis_complete_messages():
    redis_client = get_redis_client()
    ps = redis_client.pubsub()
    ps.subscribe('image_analysis_complete_ch')
    logging.info("Subscribed to image_analysis_complete_ch")

    while True:
        message = ps.get_message(ignore_subscribe_messages=True, timeout=None)
        logging.info(f"Message received from channel: {message}")

        if message is None:
            continue

        message_data: ImageAnalysisCompleteData = json.loads(message['data'])

        for handler in handlers:
            handler.handle(message_data)

if __name__ == '__main__':
    listen_for_and_process_analysis_complete_messages()
