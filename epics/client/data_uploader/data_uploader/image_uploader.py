from __future__ import annotations
from threading import Thread
from queue import Queue
import requests
from typing import TYPE_CHECKING
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

if TYPE_CHECKING:
    from .utils.types import DeviceName, InstrumentName, ShotId, TiffBytes


import logging
import tifffile
from io import BytesIO 

logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", force=True)

@dataclass
class ImageUploadData:
    device_name: DeviceName
    shot_id: ShotId
    image: np.ndarray

    def tiff_bytes(self, compression=tifffile.COMPRESSION.NONE) -> TiffBytes:
        with BytesIO() as b:
            with tifffile.TiffWriter(b) as tif:
                tif.write(self.image, description=self.device_name, compression=compression)

            return b.getvalue()

@dataclass
class MultiImageUploadData:
    instrument_name: InstrumentName
    shot_id: ShotId
    pages: list[ImageUploadData]

    def tiff_bytes(self) -> TiffBytes:
        with BytesIO() as b:
            with tifffile.TiffWriter(b) as tif:
                for image_upload_data in self.pages:
                    tif.write(image_upload_data.image, description=image_upload_data.device_name)

            return b.getvalue()


class ImageUploadThread(Thread):
    def __init__(self, queue: Queue, image_endpoint_url: str, **kwargs):
        self.queue = queue
        self.image_endpoint_url = image_endpoint_url
        super().__init__(**kwargs)

    def run(self):
        self.requests_session = requests.Session()

        try:        
            while True:
                image_upload_data = self.queue.get()
                self.upload_image(image_upload_data)

        finally:
            self.requests_session.close()

    def upload_image(self, image_upload_data: ImageUploadData | MultiImageUploadData):
        response = self.requests_session.post(self.image_endpoint_url, 
                                              data={'device_name': image_upload_data.device_name, 'shot_id': image_upload_data.shot_id},
                                              files={'image_data': image_upload_data.tiff_bytes(compression=tifffile.COMPRESSION.LZW)},
                                             )

        response_data = response.json()

        if ('message' not in response_data) or (not response_data['message'].startswith("received")):
            logging.error(f"Failed to post image data for {image_upload_data.shot_id} / {image_upload_data.device_name}: {response_data}")

        else:
            logging.info(f"Posted image data for {image_upload_data.shot_id} / {image_upload_data.device_name}")


class ImageCollector:
    """Collects images by instrument and shot and uploads them

    Some instruments are composed of multiple cameras/devices, and these images 
    should be uploaded together. 

    This class creates a multi-page tiff file from images from the same shot of 
    the same instrument and uploads it when all images are present.

    """
    
    def __init__(self, image_upload_thread: ImageUploadThread, instrument_device_map: dict[InstrumentName, list[DeviceName]]):
        self.image_upload_thread = image_upload_thread
        self.instrument_device_map = instrument_device_map
        self.generate_reverse_instrument_device_map()

        self.instrument_shot_image_data: dict[tuple[InstrumentName, ShotId], dict[DeviceName, ImageUploadData]] = defaultdict(dict)

    def generate_reverse_instrument_device_map(self):
        self.device_instrument_map = {}
        for instrument, devices in self.instrument_device_map.items():
            for device in devices:
                if device in self.device_instrument_map:
                    raise ValueError(f"Device {device} is in more than one instrument.")
                self.device_instrument_map[device] = instrument

    def instrument_has_all_device_images_for_shot(self, instrument: InstrumentName, shot_id: ShotId):
        return all(device in self.instrument_shot_image_data[(instrument, shot_id)] for device in self.instrument_device_map[instrument])

    def put_completed_instrument_data_in_upload_queue(self, instrument: InstrumentName, shot_id: ShotId):
        instrument_image_data = MultiImageUploadData(instrument, shot_id, 
                                                     [self.instrument_shot_image_data[(instrument, shot_id)][device_name]
                                                      for device_name in self.instrument_device_map[instrument]
                                                     ]
                                                    )
        self.image_upload_thread.queue.put(instrument_image_data)
        del self.instrument_shot_image_data[(instrument, shot_id)]

    def put(self, image_upload_data: ImageUploadData):
        """ Add an image and upload it if all images for the instrument/shot are present
        
        Parameters
        ----------
        image_upload_data : ImageUploadData
            Single device image data
        """

        try:
            instrument = self.device_instrument_map[image_upload_data.device_name]
        except KeyError:
            raise ValueError(f"Device {image_upload_data.device_name} is not in any instrument.")

        self.instrument_shot_image_data[(instrument, image_upload_data.shot_id)][image_upload_data.device_name] = image_upload_data

        if self.instrument_has_all_device_images_for_shot(instrument, image_upload_data.shot_id):
            self.put_completed_instrument_data_in_upload_queue(instrument, image_upload_data.shot_id)
