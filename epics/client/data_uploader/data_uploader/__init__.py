from __future__ import annotations

from datetime import datetime, timedelta, timezone
UTC = timezone.utc
from functools import partial
from time import sleep

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", force=True)

# for image uploader
from io import BytesIO
from tifffile import imwrite as write_tiff
import requests
requests_session = requests.Session()

# get environment variables, specifically image endpoint url
from os import environ as env

# EPICS channel access and pvAccess
from epics import caget, camonitor, camonitor_clear
from p4p.client.thread import Context as P4PThreadContext
pva = P4PThreadContext('pva')

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..utils.types import DeviceName, PVName
    from p4p.nt import NTNDArray
    from p4p.client.thread import Subscription as P4PSubscription

# objects representing images and scalars
from measurement_db.orm.tables import ImageDevice, Variable

PV_NAMES: dict[str, PVName] = {
    'burst_status': "Timing:TriggerGeneration:Status",
    'burst_timestamp': "Timing:TriggerGeneration:BurstTimestamp",
    'burst_frequency': "Timing:TriggerGeneration:Frequency_GET",
    'burst_num_shots': "Timing:TriggerGeneration:NumShots",
}


class DataAcquisition:
    """ An app that monitors image and scalar PVs and handles them
    
    """
    def __init__(self):

        # burst attributes relating to PVs set in the user interface
        self.burst_status: str = ""
        self.burst_timestamp: datetime = datetime.fromtimestamp(0, tz=UTC)
        self.burst_frequency: float = 0.0
        self.burst_num_shots: int = 0

        # scalars and image_devices to monitor
        self.scalars: list[Variable] = self.load_scalar_pv_list()
        self.image_devices: list[ImageDevice] = self.load_image_pv_list()
        
        # will hold pvAccess subscriptions (Channel Access subscriptions are held 
        # in epics._PVmonitors_ )
        self.subscriptions: dict[PVName, P4PSubscription] = {}

        # whether to run callbacks. mainly to prevent callbacks from running when 
        # they are called while setting up monitors.
        self.enable_callbacks = False

        logging.info(f"DataAcquisition ready to run.")

    def run(self) -> None:
        """ Start monitors and listen forever.
        """

        # don't run callback code when they are called during monitor setup
        self.enable_callbacks = False

        # subscribe to burst variables provided by user interface (through CALab)
        for pv_alias, callback_fun in [
                ('burst_status', self.burst_status_monitor_callback),
                ('burst_timestamp', self.burst_timestamp_monitor_callback),
                ('burst_frequency', self.burst_frequency_monitor_callback),
                ('burst_num_shots', self.burst_num_shots_monitor_callback),
            ]:

            camonitor(PV_NAMES[pv_alias], callback=callback_fun)
            logging.info(f"Monitoring {PV_NAMES[pv_alias]} over Channel Access")

        # subscribe to PVs in IOCs
        self.subscribe_to_image_pvs()
        self.subscribe_to_scalar_pvs()

        # re-enable callback code after the callbacks for monitor creation have 
        # been called.
        sleep(0.1)
        self.enable_callbacks = True

        try:
            while True:
                sleep(1e9)
        finally:
            self.close()

    def close(self) -> None:
        """ Close subscriptions
        """
        camonitor_clear(PV_NAMES['burst_status'])
        camonitor_clear(PV_NAMES['burst_timestamp'])
        
        for pv_name, subscription in self.subscriptions.items():
            subscription.close()
            logging.info(f"Closed subscription for {pv_name}")


    def load_image_pv_list(self) -> list[ImageDevice]:
        """ TODO: replace by database query
        """
        return [
            ImageDevice(name='E:Spectrometer:LowEnergy', image_pv_name="E:Pva:Spectrometer:LowEnergy:Image"),
            ImageDevice(name='E:Spectrometer:HighEnergy', image_pv_name="E:Pva:Spectrometer:HighEnergy:Image"),
            ImageDevice(name='E:Spectrometer:Pointing', image_pv_name="E:Pva:Spectrometer:Pointing:Image"),
        ]

    def load_scalar_pv_list(self) -> list[Variable]:
        """ TODO: replace by database query
        """
        return [
            Variable(name="Plasma:PressureControl:Pressure"),
        ]

    def subscribe_to_image_pvs(self) -> None:
        """ Add pvAccess monitors for image devices
        """
        for image_device in self.image_devices:
            self.subscriptions[image_device.image_pv_name] = \
                pva.monitor(image_device.image_pv_name, partial(self.image_pv_callback, image_device))
            logging.info(f"Monitoring {image_device.image_pv_name} over pvAccess")

            # Add a counter attribute to the ImageDevice instance
            image_device.counter = 0

    def subscribe_to_scalar_pvs(self) -> None:
        """ TODO
        """
        pass

    def burst_status_monitor_callback(self, value: str = "", **kwargs) -> None:
        """ Callback when status PV changes

        camonitor's callback arguments are keyword arguments including pvname, 
        value, char_value. 
        """

        previous_status = self.burst_status
        self.burst_status = value
        logging.info(f"Status changed to {value}.")        

        if not self.enable_callbacks:
            return

        # detect change from not running to running
        if previous_status.lower() != "running" and self.burst_status.lower() == "running":
            # reset scalar and image device counters
            self.reset_counters()

    def burst_frequency_monitor_callback(self, value: float, **kwargs) -> None:
        """ Callback when burst frequency PV changes 
        
        No need to check self.enable_callbacks: this needs to run on monitor creation
        callback.
        """

        self.burst_frequency = value
        logging.info(f"Burst frequency changed to {value}.")

    def burst_num_shots_monitor_callback(self, value: int, **kwargs) -> None:
        """ Callback when burst number of shots PV changes

        No need to check self.enable_callbacks: this needs to run on monitor creation
        callback.
        """

        self.burst_num_shots = value
        logging.info(f"Burst number of shots changed to {value}.")


    def burst_timestamp_monitor_callback(self, value: str = "", **kwargs) -> None:
        """ Callback when the burst timestamp PV changes

        camonitor's callback arguments are keyword arguments including pvname, 
        value, char_value. 
        
        Parameters
        ----------
        value : str
            Unix millisecond timestamp. The PV is of stringout type because the 
            int64 that's required can't be sent over Channel Access, which is 
            what the UI uses.

        """
        if not self.enable_callbacks:
            return

        timestamp_ms = int(value)
        self.burst_timestamp = datetime.fromtimestamp(timestamp_ms / 1e3, tz=UTC)
        # also update frequency and num_shots
        self.burst_frequency = caget(PV_NAMES['burst_frequency'])
        self.burst_num_shots = caget(PV_NAMES['burst_num_shots'])

        logging.info(f"BurstTimestamp changed to {self.burst_timestamp:%Y-%m-%d %H:%M:%S.%f}. Frequency = {self.burst_frequency} Hz, NumShots = {self.burst_num_shots}")

    def reset_counters(self):
        for scalar in self.scalars:
            scalar.counter = 0

        for image_device in self.image_devices:
            image_device.counter = 0

        logging.info("Counters reset.")


    def image_pv_callback(self, image_device: ImageDevice, image_data: NTNDArray) -> None:
        """ Upload tiff-formatted image data to image backend.
        """

        if not self.enable_callbacks:
            return

        # increase shot counter
        image_device.counter += 1

        # determine shot datetime and shot id
        shot_datetime = self.burst_timestamp + timedelta(seconds=image_device.counter / self.burst_frequency)

        shot_id = f"burst-{self.burst_timestamp:%Y-%m-%dT%H-%M-%S-%fZ}/shot-{shot_datetime:%Y-%m-%dT%H-%M-%S-%fZ}"

        # convert NDArray to tiff file byte array
        tiff_bytes = BytesIO()    
        write_tiff(tiff_bytes, image_data)
        tiff_bytes.seek(0)

        # fire POST request
        response = requests_session.post(env['IMAGE_BACKEND_ENDPOINT_URL'], 
                                         data={'device_name': image_device.name, 'shot_id': shot_id},
                                         files={'image_data': tiff_bytes},
                                        )

        response_data = response.json()

        if ('message' not in response_data) or (not response_data['message'].startswith("received")):
            logging.error(f"Failed to post image data for {shot_id} / {image_device.name}: {response_data}")

        else:
            logging.info(f"Posted image data for {shot_id} / {image_device.name}")


    def scalar_pv_callback(self, scalar: Variable, value: float) -> None:
        """ TODO
        """
        if not self.enable_callbacks:
            return
        

