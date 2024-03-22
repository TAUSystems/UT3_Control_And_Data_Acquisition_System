from __future__ import annotations

from datetime import datetime, timedelta, timezone
from numbers import Number
UTC = timezone.utc
from functools import partial
from time import sleep
import re

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", force=True)

# for image uploader
from io import BytesIO
from tifffile import imwrite as write_tiff
import requests
requests_session = requests.Session()

# get environment variables, specifically image endpoint url
from .utils.env import get_env
env = get_env(os=True, dotenv=True)

# EPICS channel access and pvAccess
from epics import caput, caget, caget_many, cainfo, camonitor, camonitor_clear
from p4p.client.thread import Context as P4PThreadContext
pva = P4PThreadContext('pva')

from .utils.types import BurstStatus

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .utils.types import DeviceName, PVName
    from p4p.nt import NTNDArray, NTBase
    from p4p.client.thread import Subscription as P4PSubscription

# objects representing images and scalars
from measurement_db.orm.tables import ImageDevice, Variable
from measurement_db.orm.tables import Session, Scan, Burst, Shot, Measurement
from measurement_db.orm.tables import VariableSource, EPICSAccessProtocol
from measurement_db.utils import get_sqlalchemy_engine
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy import select

sqlalchemy_engine = get_sqlalchemy_engine()

PV_NAMES: dict[str, PVName] = {
    'burst_status': "Timing:TriggerGeneration:Status",
    'burst_timestamp': "Timing:TriggerGeneration:BurstTimestamp",
    'burst_frequency': "Timing:TriggerGeneration:Frequency_GET",
    'burst_num_shots': "Timing:TriggerGeneration:NumShots",

    'session_title': "Timing:TriggerGeneration:SessionID",
    'scan_number': "Timing:TriggerGeneration:ScanNumber",
    'scan_description': "Timing:TriggerGeneration:ScanTitle",

    'fetch_trigger_pv': "E:Spectrometer:Pointing:ArrayCounter_RBV",
}


class DataUploader:
    """ An app that monitors image and scalar PVs and handles them

    """
    def __init__(self):

        # Current burst, session, and scan information
        self.session = Session(timestamp=datetime.now(tz=UTC), title="default", description="This session is used if UI SessionID is not yet set.")
        self.scan = Scan(timestamp=datetime.now(tz=UTC), session=self.session, description="Scan-000 default", seq=0, notes="This scan is used if no Scan is known.")
        self.burst = Burst()

        # disconnected, idle, preparing, armed, running
        self.burst_status: BurstStatus = BurstStatus.Disconnected

        # scalars and image_devices to monitor
        self.variables: list[Variable] = self.load_scalar_pv_list()
        self.image_devices: list[ImageDevice] = self.load_image_pv_list()

        # will hold pvAccess subscriptions (Channel Access subscriptions are held 
        # in epics._PVmonitors_ )
        self.subscriptions: dict[PVName, P4PSubscription] = {}

        # whether to run callbacks. mainly to prevent callbacks from running when 
        # they are called while setting up monitors.
        self.enable_callbacks = False

        logging.info(f"DataUploader ready to run.")

    def run(self) -> None:
        """ Start monitors and listen forever.
        """

        # don't run callback code when they are called during monitor setup
        self.enable_callbacks = False

        # subscribe to session, scan, burst variables provided by user interface (through CALab)
        for pv_alias, callback_fun in [
                ('burst_status', self.burst_status_monitor_callback),
                ('burst_timestamp', self.burst_timestamp_monitor_callback),
                ('burst_frequency', self.burst_frequency_monitor_callback),
                ('burst_num_shots', self.burst_num_shots_monitor_callback),
                ('session_title', self.session_title_monitor_callback),
                ('scan_description', self.scan_description_monitor_callback),
            ]:

            camonitor(PV_NAMES[pv_alias], callback=callback_fun)
            logging.info(f"Monitoring {PV_NAMES[pv_alias]} over Channel Access")

        # subscribe to PVs in IOCs
        self.subscribe_to_image_pvs()
        self.subscribe_to_scalar_pvs()

        # make sure our burst status type matches the mbbo PV values
        self.check_burst_status_enum()

        # subscribe to a trigger PV, whose callback fetches values from PVs that 
        # are not monitored but should be saved
        self.fetch_trigger_variable = Variable(name=PV_NAMES['fetch_trigger_pv'])

        try:
            self.subscriptions[self.fetch_trigger_variable] = pva.monitor(self.fetch_trigger_variable.name, self.fetch_trigger_pv_monitor_callback)
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

        # unsubscribe to session, scan, burst variables provided by user interface (through CALab)
        for pv_alias in [
                'burst_status',
                'burst_timestamp',
                'burst_frequency',
                'burst_num_shots',
                'session_title',
                'scan_number',
            ]:

            camonitor_clear(PV_NAMES[pv_alias])
            logging.info(f"Closed Channel Access subscription for {PV_NAMES[pv_alias]}")


        for pv_name, subscription in self.subscriptions.items():
            subscription.close()
            logging.info(f"Closed subscription for {pv_name}")


    def load_image_pv_list(self) -> list[ImageDevice]:
        """ 
        """
        with SQLAlchemySession(sqlalchemy_engine) as sa_session:
             return sa_session.scalars(select(ImageDevice)).all()


    def load_scalar_pv_list(self) -> list[Variable]:
        """ 
        """
        with SQLAlchemySession(sqlalchemy_engine) as sa_session:
             variables = sa_session.scalars(select(Variable)).all()

        cainfo_regex = re.compile(r"(\w+)\s+=\s([^\n]+)\n")
        def parse_cainfo(cainfo_str: str) -> dict:
            return dict(cainfo_regex.findall(cainfo_str))

        # collect variable information, such as whether it can be found on the 
        # network, whether it's numeric, etc.
        # TODO: split by Channel Access, pvAccess
        print("Collecting variable information...")
        variable_values = caget_many([variable.name for variable in variables])
        for variable, variable_value in zip(variables, variable_values):
            # TODO: periodically check whether variable has come online
            variable.is_online = (variable_value is not None)
            variable.is_numeric = isinstance(variable_value, Number)
            variable.info = {}
            if variable.is_online:
                try:
                    variable.info = parse_cainfo(cainfo(variable.name, print_out=False))
                    logging.info(f"Got cainfo for {variable.name}")
                except Exception as err:
                    variable.info = {}
                    logging.error(f"Unable to get cainfo for {variable.name}")

        return variables

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
            self.subscriptions[image_device.image_pv_name] = \
                pva.monitor(image_device.image_pv_name, partial(self.image_pv_callback, image_device))
            logging.info(f"Monitoring {image_device.image_pv_name} over pvAccess")

            # Add a counter attribute to the ImageDevice instance
            image_device.counter = 0

    def subscribe_to_scalar_pvs(self) -> None:
        """ TODO: split by Channel Access and PVAccess
        """
        for variable in self.variables:
            if variable.source == VariableSource.monitor:
                # diable monitor deadband: make sure monitor is posted even if value doesn't change
                caput(variable.name + ".MDEL", -1)
                camonitor(variable.name, callback=partial(self.scalar_pv_callback, variable))
                logging.info(f"Monitoring {variable.name} over Channel Access")

            # Add a counter attribute to the Variable instance
            variable.counter = 0


    def fetch_trigger_pv_monitor_callback(self, value: NTBase) -> None:
        """
        """
        if not self.enable_callbacks:
            return

        try:
            variables_to_fetch = filter(lambda variable: variable.is_online and variable.is_numeric, self.variables)
            shot = self.burst.shots[self.fetch_trigger_variable.counter]

            with SQLAlchemySession(sqlalchemy_engine) as sa_session:
                for variable, value in zip(variables_to_fetch, caget_many([variable.name for variable in variables_to_fetch])):
                    sa_session.add(Measurement(variable=variable, shot=shot, value=value))

                sa_session.commit()

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

            timestamp_ms = int(value)
            self.burst.timestamp = datetime.fromtimestamp(timestamp_ms / 1e3, tz=UTC)

            # some burst attributes can be not set if the UI started before the uploader
            # TODO: This is unexpected, because starting the monitor should set these
            # attributes.
            if self.burst.repetition_rate is None:
                self.burst.repetition_rate = caget(PV_NAMES['burst_frequency'])
            if self.burst.number_of_shots is None:
                self.burst.number_of_shots = caget(PV_NAMES['burst_num_shots'])

            logging.info(f"BurstTimestamp changed to {self.burst.timestamp:%Y-%m-%d %H:%M:%S.%f}. Frequency = {self.burst.repetition_rate} Hz, NumShots = {self.burst.number_of_shots}")

            self.burst = Burst(timestamp=self.burst.timestamp, 
                            scan=self.scan, 
                            seq=self.burst.seq, 
                            number_of_shots=self.burst.number_of_shots,
                            repetition_rate=self.burst.repetition_rate,
                            )

            self.burst.shots = [
                Shot(timestamp = self.burst.timestamp + timedelta(seconds=seq / self.burst.repetition_rate),
                     seq = seq,
                    ) for seq in range(1, self.burst.number_of_shots + 1)
                ]

            with SQLAlchemySession(sqlalchemy_engine) as sa_session:
                sa_session.add(self.burst)
                sa_session.commit()

        except Exception as err:
            logging.error(f"Unable to create burst and shots: {err}")

        finally:
            self.burst.seq += 1

    def session_title_monitor_callback(self, value: str, **kwargs):
        self.session = Session(title=value)
        logging.info(f"New session \"{self.session.title}\"")

        if not self.enable_callbacks:
            return

        with SQLAlchemySession(sqlalchemy_engine) as sa_session:
            sa_session.add(self.session)
            sa_session.commit()


    def scan_description_monitor_callback(self, value: str, **kwargs):

        # Scan description should start with Scan 123 (hyphen/underscore allowed)
        if (m := re.match(r"Scan[ _\-](?P<seq>\d{3})", value)) is None:
            seq = -1
            logging.error(f"Scan description \"{value}\" does not start with Scan XXX")
        else:
            seq = int(m['seq'])
        self.scan = Scan(description=value, seq=seq, session=self.session)
        logging.info(f"New scan, number {self.scan.seq} with description \"{self.scan.description}\"")
        self.burst.seq = 1

        if not self.enable_callbacks:
            return

        with SQLAlchemySession(sqlalchemy_engine) as sa_session:
            sa_session.add(self.scan)
            sa_session.commit()


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
            shot_datetime = self.burst.timestamp + timedelta(seconds=image_device.counter / self.burst.repetition_rate)

            shot_id = f"burst-{self.burst.timestamp:%Y-%m-%dT%H-%M-%S-%fZ}/shot-{shot_datetime:%Y-%m-%dT%H-%M-%S-%fZ}"

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
            shot = self.burst.shots[variable.counter]
            with SQLAlchemySession(sqlalchemy_engine) as sa_session:
                sa_session.add(Measurement(variable=variable, shot=shot, value=value))
                sa_session.commit()

        except Exception as err:
            logging.error(f"Error in scalar_pv_callback: {err}")

        finally:
            # increase shot counter
            variable.counter += 1
