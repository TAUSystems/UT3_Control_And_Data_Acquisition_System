from __future__ import annotations
from typing import TYPE_CHECKING, Callable

import json

# TODO: logging config file
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", force=True)

from image_analysis_complete_handler.utils.env import get_env
from image_analysis_complete_handler.utils.types import ImageAnalysisCompleteData, ImageDeviceDirectoryEntry
from image_analysis_complete_handler.handlers.last_analyzed_shotid_pv import PopulateLastAnalyzedShotIDPV
from image_analysis_complete_handler.handlers.analysis_folder_links import CreateAnalysisFolderLinks
if TYPE_CHECKING:
    from image_analysis_complete_handler.handlers.base import ImageAnalysisCompleteHandler

import pika

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
    CreateAnalysisFolderLinks(env.get('RESULTS_STORAGE_BASE_DIRECTORY')),
]

def get_image_analysis_complete_channel(callback: Callable) -> pika.channel.Channel:
    exchange_name = "image_analysis_complete_ch"
    queue_name = "image_analysis_complete_handler"
    virtual_host = "image-analysis-complete"

    credentials = pika.PlainCredentials(env['IMAGE_ANALYSIS_COMPLETE_CH_USERNAME'], env['IMAGE_ANALYSIS_COMPLETE_CH_PASSWORD'])
    connection = pika.BlockingConnection(pika.ConnectionParameters(host = env['IMAGE_ANALYSIS_COMPLETE_CH_HOST'], port = env['IMAGE_ANALYSIS_COMPLETE_CH_PORT'], credentials = credentials, virtual_host=virtual_host))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
    channel.queue_declare(queue=queue_name, exclusive=True)
    channel.queue_bind(exchange=exchange_name, queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    return channel

def message_received_callback(ch, method, properties, body):

    logging.info(f"Message received from channel: {body}")

    if body is None:
        return

    message_data: ImageAnalysisCompleteData = json.loads(body)

    for handler in handlers:
        try:
            handler.handle(message_data)
            logging.info(f"Message for {message_data['shot_id']} / {message_data['device_name']} handled by {handler.__class__.__name__}")
        except Exception as err:
            logging.error(f"Error handling message for {message_data['shot_id']} / {message_data['device_name']} by {handler.__class__.__name__}: {err}")


def listen_for_and_process_analysis_complete_messages():
    
    channel = get_image_analysis_complete_channel(message_received_callback)
    logging.info("Subscribed to image_analysis_complete_ch")
    channel.start_consuming()

 
if __name__ == '__main__':
    listen_for_and_process_analysis_complete_messages()
