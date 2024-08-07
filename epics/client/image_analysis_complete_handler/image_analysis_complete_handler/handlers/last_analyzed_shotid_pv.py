from __future__ import annotations
from typing import TYPE_CHECKING

import json

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", force=True)

if TYPE_CHECKING:
    from ..utils.types import ImageAnalysisCompleteData, DeviceName, PVName
from .base import ImageAnalysisCompleteHandler

from epics import caput

class PopulateLastAnalyzedShotIDPV(ImageAnalysisCompleteHandler):

    DEFAULT_LAST_ANALYZED_PV_NAMES: dict[DeviceName, PVName] = {
        "E:Spectrometer:LowEnergy": "E:Spectrometer:LastAnalyzedShotID",
        "E:Spectrometer": "E:Spectrometer:LastAnalyzedShotID",
    }

    def __init__(self, last_analyzed_pv_names: dict[DeviceName, PVName] = None):
        if last_analyzed_pv_names:
            self.last_analyzed_pv_names = last_analyzed_pv_names
        else:
            self.last_analyzed_pv_names = self.DEFAULT_LAST_ANALYZED_PV_NAMES

        super().__init__()
    
    def handle(self, message_data: ImageAnalysisCompleteData) -> None:

        try:
            last_analyzed_pv_name = self.last_analyzed_pv_names[message_data['device_name']]
        except (KeyError, AttributeError):
            logging.warning(f"No LastAnalyzed PV for device {message_data['device_name']}")
            return

        if last_analyzed_pv_name is not None:
            try:
                logging.info(f"running caput({last_analyzed_pv_name}, {message_data.get('shot_id')})")  
                # p4p_context.put(last_analyzed_pv_name, image_finished_message.get('shot_id'))
                caput(last_analyzed_pv_name + '.$', str(message_data.get('shot_id')) )
                logging.info(f"Set PV {last_analyzed_pv_name} to '{message_data.get('shot_id')}'")
            except TimeoutError:
                logging.error(f"Could not find PV {last_analyzed_pv_name}")
