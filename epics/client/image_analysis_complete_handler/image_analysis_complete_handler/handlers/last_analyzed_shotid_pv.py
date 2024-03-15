from __future__ import annotations
from typing import TYPE_CHECKING

import json

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", force=True)

if TYPE_CHECKING:
    from ..utils.types import ImageAnalysisCompleteMessage, DeviceName, PVName
from .base import ImageAnalysisCompleteHandler

from epics import caput

class PopulateLastAnalyzedShotIDPV(ImageAnalysisCompleteHandler):

    DEFAULT_LAST_ANALYZED_PV_NAMES: dict[DeviceName, PVName] = {
        "E:Spectrometer:LowEnergy": "E:Spectrometer:LastAnalyzedShotID",
    }

    def __init__(self, last_analyzed_pv_names: dict[DeviceName, PVName] = None):
        if last_analyzed_pv_names:
            self.last_analyzed_pv_names = last_analyzed_pv_names
        else:
            self.last_analyzed_pv_names = self.DEFAULT_LAST_ANALYZED_PV_NAMES

        super().__init__()
    
    def handle(self, message: ImageAnalysisCompleteMessage) -> None:

        image_finished_message = json.loads(message['data'])
	
        try:
            last_analyzed_pv_name = self.LAST_ANALYZED_PV_NAMES[image_finished_message['device_name']]
        except (KeyError, AttributeError):
            logging.warning(f"No LastAnalyzed PV for device {image_finished_message['device_name']}")
            return

        if last_analyzed_pv_name is not None:
            try:
                logging.info(f"running caput({last_analyzed_pv_name}, {image_finished_message.get('shot_id')})")  
                # p4p_context.put(last_analyzed_pv_name, image_finished_message.get('shot_id'))
                caput(last_analyzed_pv_name + '.$', str(image_finished_message.get('shot_id')) )
                logging.info(f"Set PV {last_analyzed_pv_name} to '{image_finished_message.get('shot_id')}'")
            except TimeoutError:
                logging.error(f"Could not find PV {last_analyzed_pv_name}")
