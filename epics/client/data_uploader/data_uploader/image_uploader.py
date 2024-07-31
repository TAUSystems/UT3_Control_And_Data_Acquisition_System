from __future__ import annotations
from threading import Thread
from queue import Queue
import requests
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .utils.types import ImageUploadData

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", force=True)

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

    def upload_image(self, image_upload_data: ImageUploadData):
        response = self.requests_session.post(self.image_endpoint_url, 
                                              data={'device_name': image_upload_data.device_name, 'shot_id': image_upload_data.shot_id},
                                              files={'image_data': image_upload_data.image_data},
                                             )

        response_data = response.json()

        if ('message' not in response_data) or (not response_data['message'].startswith("received")):
            logging.error(f"Failed to post image data for {image_upload_data.shot_id} / {image_upload_data.device_name}: {response_data}")

        else:
            logging.info(f"Posted image data for {image_upload_data.shot_id} / {image_upload_data.device_name}")
