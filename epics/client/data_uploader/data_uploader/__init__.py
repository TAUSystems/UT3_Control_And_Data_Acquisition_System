from __future__ import annotations

from datetime import datetime, timedelta, timezone
from numbers import Number
UTC = timezone.utc
from functools import partial
from time import sleep
import re
from enum import Enum

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", force=True)

# for image uploader
from io import BytesIO
from tifffile import imwrite as write_tiff
import requests

# get environment variables, specifically image endpoint url
from .utils.env import get_env
env = get_env(os=True, dotenv=True)

# EPICS channel access and pvAccess
from epics import caget_many
from epics.pv import PV
from p4p.client.thread import Context as P4PThreadContext
pva = P4PThreadContext('pva')

from .utils.types import BurstStatus

from typing import TYPE_CHECKING, Type
if TYPE_CHECKING:
    from .utils.types import DeviceName, PVName
    from p4p.nt import NTNDArray, NTBase
    from p4p.client.thread import Subscription as P4PSubscription

# objects representing images and scalars
from measurement_db.orm.tables import ImageDevice, Variable
from measurement_db.orm.tables import Session, Scan, Burst, Shot, Measurement
from measurement_db.orm.tables import VariableSource, EPICSAccessProtocol
from measurement_db.utils import get_sqlalchemy_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import select

sqlalchemy_engine = get_sqlalchemy_engine()
sqlalchemy_session_factory = sessionmaker(sqlalchemy_engine, expire_on_commit=False)
SQLAlchemySession = scoped_session(sqlalchemy_session_factory)

# these are the PVs necessary for operating this DataUploader
PV_NAMES: dict[str, PVName] = {
    'burst_status': "Timing:TriggerGeneration:Status",
    'burst_timestamp': "Timing:TriggerGeneration:BurstTimestamp",
    'burst_frequency': "Timing:TriggerGeneration:Frequency_GET",
    'burst_num_shots': "Timing:TriggerGeneration:NumShots",

    'session_title': "Data:Scan:Session",
    'scan_number': "Data:Scan:Number",
    'scan_title': "Data:Scan:Title",

    'fetch_trigger_pv': "E:Spectrometer:Pointing:ArrayCounter_RBV",
}


class DataUploader:
    """ An app that monitors image and scalar PVs and handles them

    """
    def __init__(self):

        # Current burst, session, and scan information
        self.session = Session(timestamp=datetime.now(tz=UTC), title="default", description="This session is used if UI SessionID is not yet set.")
        self.scan = Scan(timestamp=datetime.now(tz=UTC), session=self.session, description="Scan-000 default", seq=0, notes="This scan is used if no Scan is known.")
        self.burst = Burst(timestamp=datetime.now(tz=UTC), repetition_rate=None, number_of_shots=None, seq=0)

        # disconnected, idle, preparing, armed, running
        self.burst_status: BurstStatus = BurstStatus.Disconnected
        self.current_burst_seq: int = 1

        # scalars and image_devices to monitor
        # PVs to monitor for the operation of this Data Uploader
        self.burst_pvs: dict[str, PV] = {}
        # scalars whose measurements will be saved
        self.variables: list[Variable] = []
        # images to be sent to image backend
        self.image_devices: list[ImageDevice] = []

        # Session for image upload HTTP Requests. 
        # People on the internet seem to be uncertain how thread-safe this is, 
        # so it should be good enough for my purposes.
        self.requests_session = requests.Session()

        # will hold pvAccess subscriptions (Channel Access subscriptions are held 
        # in epics._PVmonitors_ )
        self.subscriptions: dict[PVName, P4PSubscription] = {}

        # whether to run callbacks. mainly to prevent callbacks from running when 
        # they are called while setting up monitors.
        self.enable_callbacks: bool = False

        logging.info(f"DataUploader ready to run.")

    def run(self) -> None:
        """ Start monitors and listen forever.
        """

        # don't run callback code when they are called during monitor setup
        self.enable_callbacks = False

        # Load scalars and image devices from measurement database
        self.load_scalar_pv_list()
        self.load_image_pv_list()

        # subscribe to burst PVs
        self.subscribe_to_burst_pvs()

        # subscribe to PVs in IOCs
        self.subscribe_to_image_pvs()
        self.subscribe_to_scalar_pvs()

        # make sure our burst status type matches the mbbo PV values
        self.check_burst_status_enum()

        # subscribe to a trigger PV, whose callback fetches values from PVs that 
        # are not monitored but should be saved
        self.fetch_trigger_variable = Variable(name=PV_NAMES['fetch_trigger_pv'])

        try:
            self.subscriptions[self.fetch_trigger_variable.name] = pva.monitor(self.fetch_trigger_variable.name, self.fetch_trigger_pv_monitor_callback)
            self.fetch_trigger_variable.counter = 0
            # camonitor(self.fetch_trigger_variable.name, callback=self.fetch_trigger_pv_monitor_callback)
            logging.info(f"Monitoring {self.fetch_trigger_variable.name} over Channel Access")

        except Exception as err:
            logging.error(f"Failed to monitor {self.fetch_trigger_variable.name} over Channel Access: {err}")

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

        # unsubscribe to scalar variables
        for variable in self.variables:
            if hasattr(variable, 'pv') and variable.pv is not None:
                variable.pv.clear_callbacks()
                logging.info(f"Closed Channel Access subscriptions for {variable.name}")

        # unsubscribe to images
        for image_device in self.image_devices:
            if hasattr(image_device, 'pva_monitor') and image_device.pva_monitor is not None:
                image_device.pva_monitor.close()
                logging.info(f"Closed PVAccess subscription for {image_device.name}")

        # unsubscribe to burst variables
        for pv_alias, pv in self.burst_pvs.items():
            pv.clear_callbacks()
            logging.info(f"Closed Channel Access subscriptions for {pv.pvname}")

    def load_image_pv_list(self) -> None:
        """ 
        """
        with SQLAlchemySession() as sa_session:
             self.image_devices = sa_session.scalars(select(ImageDevice)).all()


    def load_scalar_pv_list(self) -> None:
        """ 
        """
        with SQLAlchemySession() as sa_session:
             self.variables = sa_session.scalars(select(Variable)).all()


    def subscribe_to_scalar_pvs(self) -> None:

        # cainfo is a string that looks like 

        cainfo_regex = re.compile(r"(\w+)\s+=\s([^\n]+)\n")
        def parse_cainfo(cainfo_str: str) -> dict:
            return dict(cainfo_regex.findall(cainfo_str))

        def parse_dtype(fulltype: str) -> Type:
            """
            From https://github.com/pyepics/pyepics/blob/0b33db782dde77d89ee847bee4e6fc314bc3c30b/epics/pv.py#L873
            """
            if '_' in fulltype:
                mod, xtype = fulltype.split('_')
            else:
                xtype = fulltype

            return {'string': str,
                    'char': str,
                    'float': float,
                    'double': float,
                    'long': int,
                    'enum': Enum,
                    'bool': bool,
                   }[xtype]

        # collect variable information, such as whether it can be found on the 
        # network, whether it's numeric, etc.
        # TODO: split by Channel Access, pvAccess
        print("Collecting variable information...")
        for variable in self.variables:

            if variable.source == VariableSource.monitor:
                variable.pv = PV(variable.name, callback=partial(self.scalar_pv_callback, variable))
                # disable monitor deadband: make sure monitor is posted even if value doesn't change
                PV(variable.name + ".MDEL").put(-1)
                logging.info(f"Monitoring {variable.name} over Channel Access")

            elif variable.source == VariableSource.fetch:
                variable.pv = PV(variable.name, auto_monitor=False)

            variable.info = {}
            info = variable.pv.info
            if info is not None:
                variable.info = parse_cainfo(info)
                variable.dtype = parse_dtype(info['type'])
                logging.info(f"Got cainfo for {variable.name}")
            else:
                variable.dtype = None
                logging.warning(f"Unable to get cainfo for {variable.name}")

            # Add a counter attribute to the Variable instance
            variable.counter = 0


    def check_burst_status_enum(self) -> None:
        """
        """
        mbbo_string_field_names = ['ZRST', 'ONST', 'TWST', 'THST', 'FRST', 'FVST', 'SXST', 'SVST', 'EIST', 'NIST', 'TEST', 'ELST', 'TVST', 'TTST', 'FTST', 'FFST']
        status_pv_strings = caget_many([f"{PV_NAMES['burst_status']}.{mbbo_string_field_names[burst_status.value]}" 
                                        for burst_status in BurstStatus
                                      ])
        try:
            assert all([status_pv_string == burst_status.name for status_pv_string, burst_status in zip(status_pv_strings, BurstStatus)])
            logging.info(f"Checked BurstStatus enum matches {PV_NAMES['burst_status']} strings.")
        except AssertionError:
            logging.error(f"BurstStatus enum and {PV_NAMES['burst_status']} strings don't match!\n"
                          f"\tBurstStatus = {list(BurstStatus)}\n"
                          f"\t{PV_NAMES['burst_status']} = {status_pv_strings}"
                         )

    def subscribe_to_image_pvs(self) -> None:
        """ Add pvAccess monitors for image devices
        """
        for image_device in self.image_devices:
            image_device.pva_monitor = \
                pva.monitor(image_device.image_pv_name, partial(self.image_pv_callback, image_device))
            logging.info(f"Monitoring {image_device.image_pv_name} over pvAccess")

            # Add a counter attribute to the ImageDevice instance
            image_device.counter = 0

    
    def subscribe_to_burst_pvs(self) -> None:
        """
        """

        # Monitor these PVs
        for pv_alias, callbacks in [
                ('burst_status', [self.burst_status_monitor_callback]),
                ('burst_frequency', []),
                ('burst_num_shots', []),
                ('session_title', [self.session_title_monitor_callback]),
                ('scan_title', []),
                ('scan_number', [self.scan_number_monitor_callback]),
            ]:

            self.burst_pvs[pv_alias] = PV(PV_NAMES[pv_alias], callback=callbacks, )
            logging.info(f"Montitoring {PV_NAMES[pv_alias]} over Channel Access.")

        # PV connections without monitoring
        for pv_alias in ['burst_timestamp']:
            self.burst_pvs[pv_alias] = PV(PV_NAMES[pv_alias], auto_monitor=False)

    def fetch_trigger_pv_monitor_callback(self, value: NTBase) -> None:
        """
        """
        if not self.enable_callbacks:
            return

        try:
            variables_to_fetch = [variable for variable in self.variables
                                  if variable.source == VariableSource.fetch
                                     and variable.pv.connected and issubclass(variable.dtype, Number)
                                 ]

            # shot = self.burst.shots[self.fetch_trigger_variable.counter]
            values = [variable.pv.get() for variable in variables_to_fetch]
            with SQLAlchemySession() as sa_session:
                shot = sa_session.merge(self.burst.shots[self.fetch_trigger_variable.counter], load=False)
                num_measurements_inserted = 0
                for variable, value in zip(variables_to_fetch, values):
                    if value is None:
                        logging.warning(f"No value for {variable.name}. Possibly it went offline. Removing from list of variables to fetch on trigger.")
                        continue
                    variable_merged = sa_session.merge(variable, load=False)
                    sa_session.add(Measurement(variable=variable_merged, shot=shot, value=float(value)))
                    num_measurements_inserted += 1
                sa_session.commit()

            logging.info(f"Inserted {num_measurements_inserted} measurements fetched on trigger variable")

        except Exception as err:
            logging.error(f"Error fetching variables: {err}")

        finally:
            self.fetch_trigger_variable.counter += 1


    def burst_status_monitor_callback(self, value: int, **kwargs) -> None:
        """ Callback when status PV changes

        camonitor's callback arguments are keyword arguments including pvname, 
        value, char_value. 
        """

        previous_status: BurstStatus = BurstStatus(self.burst_status)
        self.burst_status: BurstStatus = BurstStatus(value)
        logging.info(f"Status changed to {value}: {self.burst_status}.")

        if not self.enable_callbacks:
            return

        # detect change from not running to running
        if previous_status != BurstStatus.Running and self.burst_status == BurstStatus.Running:
            # reset scalar and image device counters
            self.reset_counters()

    def burst_frequency_monitor_callback(self, value: float, **kwargs) -> None:
        """ Callback when burst frequency PV changes 

        No need to check self.enable_callbacks: this needs to run on monitor creation
        callback.
        """

        self.burst.repetition_rate = value
        logging.info(f"Burst frequency changed to {value}.")

    def burst_num_shots_monitor_callback(self, value: int, **kwargs) -> None:
        """ Callback when burst number of shots PV changes

        No need to check self.enable_callbacks: this needs to run on monitor creation
        callback.
        """

        self.burst.number_of_shots = value
        logging.info(f"Burst number of shots changed to {value}.")


    def burst_timestamp_monitor_callback(self, value: str, **kwargs) -> None:
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

        try:
            pva.put("TakeNShots:BurstInDB", 0)

            self.burst = Burst(timestamp=datetime.now(tz=UTC), 
                               scan=self.scan, 
                               seq=self.current_burst_seq,
                               number_of_shots=self.burst_pvs['burst_num_shots'].value,
                               repetition_rate=self.burst_pvs['burst_frequency'].value,
                              )


            for seq in range(1, self.burst.number_of_shots + 1):
                self.burst.shots.append(
                    Shot(timestamp = self.burst.timestamp + timedelta(seconds=seq / self.burst.repetition_rate),
                         seq = seq,
                        ) 
                )

            with SQLAlchemySession() as sa_session:
                sa_session.add(self.burst)
                sa_session.commit()

            pva.put("TakeNShots:BurstInDB", 1)

        except Exception as err:
            logging.error(f"Unable to create burst and shots: {err}")

    def session_title_monitor_callback(self, value: str, **kwargs):
        self.session = Session(title=value, timestamp=datetime.now(tz=UTC))
        logging.info(f"New session \"{self.session.title}\"")

        # if not self.enable_callbacks:
        #     return

        # with SQLAlchemySession() as sa_session:
        #     sa_session.add(self.session)
        #     sa_session.commit()


    def scan_number_monitor_callback(self, value: int, **kwargs):
        self.scan = Scan(timestamp=datetime.now(tz=UTC), title=self.scan.title, seq=value, session=self.session)
        logging.info(f"New scan, number {self.scan.seq} with title \"{self.scan.title}\"")
        self.current_burst_seq = 1

    def scan_title_monitor_callback(self, value: str, **kwargs):
        self.scan.title = value
        logging.info(f"Scan title set to \"{self.scan.title}\"")

    def reset_counters(self):
        for variable in self.variables:
            variable.counter = 0

        for image_device in self.image_devices:
            image_device.counter = 0

        self.fetch_trigger_variable.counter = 0

        logging.info("Counters reset.")


    def image_pv_callback(self, image_device: ImageDevice, image_data: NTNDArray) -> None:
        """ Upload tiff-formatted image data to image backend.
        """

        if not self.enable_callbacks:
            return

        try:
            # determine shot datetime and shot id
            shot_datetime = self.burst.timestamp + timedelta(seconds=(image_device.counter + 1) / self.burst.repetition_rate)

            shot_id = f"burst-{self.burst.timestamp:%Y-%m-%dT%H-%M-%S-%fZ}/shot-{shot_datetime:%Y-%m-%dT%H-%M-%S-%fZ}"

            # convert NDArray to tiff file byte array
            tiff_bytes = BytesIO()
            write_tiff(tiff_bytes, image_data)
            tiff_bytes.seek(0)

            # fire POST request
            response = self.requests_session.post(env['IMAGE_BACKEND_ENDPOINT_URL'], 
                                                  data={'device_name': image_device.name, 'shot_id': shot_id},
                                                  files={'image_data': tiff_bytes},
                                                 )

            response_data = response.json()

            if ('message' not in response_data) or (not response_data['message'].startswith("received")):
                logging.error(f"Failed to post image data for {shot_id} / {image_device.name}: {response_data}")

            else:
                logging.info(f"Posted image data for {shot_id} / {image_device.name}")

        except Exception as err:
            pass

        finally:
            # increase shot counter
            image_device.counter += 1


    def scalar_pv_callback(self, variable: Variable, value: float, **kwargs) -> None:
        """ TODO
        """
        if not self.enable_callbacks:
            return

        try:
            # shot = self.burst.shots[variable.counter]
            with SQLAlchemySession() as sa_session:
                shot = sa_session.merge(self.burst.shots[variable.counter], load=False)
                variable_merged = sa_session.merge(variable, load=False)
                sa_session.add(Measurement(variable=variable_merged, shot=shot, value=value))
                sa_session.commit()

        except Exception as err:
            logging.error(f"Error in scalar_pv_callback: {err}")

        finally:
            # increase shot counter
            variable.counter += 1
