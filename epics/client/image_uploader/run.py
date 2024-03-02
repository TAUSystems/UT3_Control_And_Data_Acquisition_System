from __future__ import annotations
from typing import TYPE_CHECKING

from io import BytesIO
from functools import partial
from datetime import datetime, timezone, timedelta
from time import sleep
from os import environ as env

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", force=True)

from tifffile import imwrite as write_tiff

import requests
requests_session = requests.Session()

# TODO: replace by config file
from utils.types import ImageDeviceDirectoryEntry

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

from epics import caget, caput

if TYPE_CHECKING:
    from p4p.nt import NTNDArray
    from p4p.client.thread import Subscription as P4PSubscription
    from utils.types import DeviceName

# work_queue = WorkQueue(WORK_QUEUE_NUM_WORKERS)
p4p_context = P4PContext('pva') #, queue=work_queue)

burst_timestamp_ms = int(datetime.now().timestamp() * 1000)

def send_to_image_backend(device_name: DeviceName, image_data: NTNDArray):
    """ Upload tiff-formatted image data to image backend.
    """
    # get shot number
    #burst_timestamp_ms, frequency_Hz, shot_index = p4p_context.get(["Timing:TriggerGeneration:BurstTimestamp_SET", 
    #                                                                "Timing:TriggerGeneration:Frequency_GET", 
    #                                                               IMAGE_DEVICES[device_name].array_counter_pv_name,
    #                                                              ])
    frequency_Hz, shot_index = 1.0, p4p_context.get(IMAGE_DEVICES[device_name].array_counter_pv_name)
    burst_datetime = datetime.fromtimestamp(burst_timestamp_ms / 1e3, timezone.utc)
    shot_datetime = burst_datetime + timedelta(seconds=shot_index / frequency_Hz)

    shot_id = f"burst-{burst_datetime:%Y-%m-%dT%H-%M-%S-%fZ}/shot-{shot_datetime:%Y-%m-%dT%H-%M-%S-%fZ}"

    # convert NDArray to tiff file byte array
    tiff_bytes = BytesIO()    
    write_tiff(tiff_bytes, image_data)
    tiff_bytes.seek(0)

    # get unique_id_pv_name by taking the image pv name, splitting off Image and adding UniqueId_RBV
    unique_id_pv_name = ':'.join(IMAGE_DEVICES[device_name].image_pv_name.split(':')[-1] + ['UniqueId_RBV'])
    logging.info(f"Sending image to backend:\n"
                 f"  {shot_id} / {device_name}\n"
                 f"  UniqueId = {p4p_context.get(unique_id_pv_name)}, Image data hash = {hash(image_data.tobytes())}"
                )

    # fire POST request
    response = requests_session.post(env['IMAGE_BACKEND_ENDPOINT_URL'], 
                                     data={'device_name': device_name, 'shot_id': shot_id},
                                     files={'image_data': tiff_bytes},
                                    )

    response_data = response.json()

    if ('message' not in response_data) or (not response_data['message'].startswith("received")):
        logging.error(f"Failed to post image data for {shot_id} / {device_name}: {response_data}")

    else:
        logging.info(f"Posted image data for {shot_id} / {device_name}")


def subscribe_to_PVs_for_upload() -> dict[DeviceName, P4PSubscription]:
    """ Start monitoring image PVs and register the upload callback to each subscription
    """
    subscriptions: dict[DeviceName, P4PSubscription] = {}
    for device_name, device_directory_entry in IMAGE_DEVICES.items():
        subscriptions[device_name] = \
            p4p_context.monitor(device_directory_entry.image_pv_name, partial(send_to_image_backend, device_name))
        logging.info(f"Monitoring {device_directory_entry.image_pv_name}.")

    return subscriptions

if __name__ == '__main__':
    subscriptions: dict[DeviceName, P4PSubscription] = subscribe_to_PVs_for_upload()
    try:
        while True:
            sleep(1e9)
    finally:
        for device_name, subscription in subscriptions.items():
            subscription.close()
            logging.info(f"Closed subscription for {device_name}")

