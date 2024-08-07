from __future__ import annotations

from datetime import datetime, timedelta, timezone
from numbers import Number
UTC = timezone.utc
from functools import partial
from time import sleep
import re
from enum import Enum
from warnings import warn
from threading import Thread, Lock
from queue import Queue, Empty

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", force=True)

# get environment variables, specifically image endpoint url
from .utils.env import get_env
env = get_env(os=True, dotenv=True)

# EPICS channel access and pvAccess
from epics import caget, caget_many
from epics.pv import PV
from p4p.client.thread import Context as P4PThreadContext
pva = P4PThreadContext('pva')

from .utils.types import BurstStatus, ScalarSaveStatus, ShotSeq

from typing import TYPE_CHECKING, Iterable, Type
if TYPE_CHECKING:
    from .utils.types import InstrumentName, DeviceName, PVName
    from p4p.nt import NTNDArray, NTBase
    from p4p.client.thread import Subscription as P4PSubscription
    from numpy.typing import NDArray

# objects representing images and scalars
from measurement_db.orm.tables import ImageDevice, Variable
from measurement_db.orm.tables import Session, Scan, Burst, Shot, Measurement

from .utils.image_analysis_backend import parse_shot_id

from .scalars_saved_tracker import ScalarsSavedTracker
from .image_uploader import ImageUploadThread, ImageCollector, ImageUploadData

# Declare types of attributes that are attached to the ORM objects
if TYPE_CHECKING:
    class Scan(Scan):
        current_burst_seq: int

    class Burst(Burst):
        shot_directory: dict[ShotSeq, Shot]
        scalars_saved_tracker: ScalarsSavedTracker

    class Variable(Variable):
        pv: PV
        info: dict
        dtype: Type
        counter: int

    class ImageDevice(ImageDevice):
        counter: int

from measurement_db.orm.tables import VariableSource
from measurement_db.utils import get_sqlalchemy_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import select

sqlalchemy_engine = get_sqlalchemy_engine()
sqlalchemy_session_factory = sessionmaker(sqlalchemy_engine, expire_on_commit=False)
SQLAlchemySession = scoped_session(sqlalchemy_session_factory)

# these are the PVs necessary for operating this DataUploader
PV_NAMES: dict[str, PVName] = {
    'burst_status': "Timing:TriggerGeneration:Status",
    'burst_frequency': "Timing:TriggerGeneration:Frequency_GET",
    'burst_num_shots': "Timing:TriggerGeneration:NumShots_GET",

    'session_timestamp': "Data:Session:Timestamp",
    'session_title': "Data:Session:Title",

    'scan_title': "Data:Scan:Title",
    'scan_number': "Data:Scan:Number",
    'scan_timestamp': "Data:Scan:Timestamp",

    'burst_timestamp': "Timing:TriggerGeneration:BurstTimestamp",

    'fetch_trigger_pv': "E:Spectrometer:Pointing:ArrayCounter_RBV",

    'fetched_scalars_ready':  "Data:Scalars:FetchedValuesReady",
    'monitored_scalars_ready':  "Data:Scalars:MonitoredValuesReady",
    'image_backend_scalars_ready':  "Data:Scalars:ImagesValuesReady",
    'all_scalars_ready':  "Data:Scalars:AllValuesReady",
}

LAST_ANALYZED_SHOT_ID_PV_NAMES: dict[DeviceName, PVName] = {
    "E:Spectrometer:LowEnergy": "E:Spectrometer:LastAnalyzedShotID",
}

# list of composite devices and their components
INSTRUMENT_DEVICE_MAP: dict[InstrumentName, list[DeviceName]] = {
    'E:Spectrometer': [
        'E:Spectrometer:Pointing',
        'E:Spectrometer:LowEnergy',
        'E:Spectrometer:HighEnergy',
    ],
}


class ScalarSaveThread(Thread):
    """ A thread to save measurements to DB and update the ScalarsSavedTracker
    """
    def __init__(self, 
                 queue: Queue[Measurement | Iterable[Measurement]], 
                 num_measurements_per_transaction = 20, 
                 no_new_measurements_timeout = 1.0, 
                 update_scalars_saved_tracker_queue: Queue = None, 
                 **kwargs
                ):
        """ 
        Parameters
        ----------
        queue : Queue[Measurement | Iterable[Measurement]]
            Measurements are read from this queue
        num_measurements_per_transaction : int, optional
            Write measurements to db only if there are at least 
            num_measurements_per_transaction of them, by default 20
        no_new_measurements_timeout : float, optional
            Write remaining measurements to db if there are no new measurements 
            in queue for this time in seconds, by default 1.0
        update_scalars_saved_tracker_queue : Queue, optional
            The queue to put measurements in that have been saved, so that the 
            scalar_saved_trackers can be updated, by default None
        """
        self.queue = queue
        self.num_measurements_per_transaction = num_measurements_per_transaction
        self.no_new_measurements_timeout = no_new_measurements_timeout

        self.update_scalars_saved_tracker_queue = update_scalars_saved_tracker_queue

        self.measurements_to_save: list[Measurement] = []

        super().__init__(**kwargs)
    
    def commit(self):
        """ Saves measurements to database and updates ScalarsSavedTracker
        """
        try:
            with SQLAlchemySession() as sa_session:
                sa_session.add_all(self.measurements_to_save)
                sa_session.commit()
            logging.info(f"Inserted {len(self.measurements_to_save)} monitored measurements.")
        except Exception as err:
            logging.error(f"Error inserting {len(self.measurements_to_save)} monitored measurements: {err}")

        self.update_scalars_saved_tracker_queue.put(self.measurements_to_save)

        # Clear measurements_to_save
        self.measurements_to_save = []

    def run(self):

        try:
            while True:
                try:
                    # raises Empty exception if no scalar data arrives within the 
                    # timeout period
                    match measurement_or_measurements := self.queue.get(timeout=self.no_new_measurements_timeout):
                        case list(measurements) if all(isinstance(measurement, Measurement) for measurement in measurements):
                            self.measurements_to_save.extend(measurements)
                        case Measurement() as measurement:
                            self.measurements_to_save.append(measurement)
                        case _:
                            raise TypeError(f"Object not of type Measurement obtained from ScalarSaveThread queue: {measurement_or_measurements}")

                    # If the number of measurements in the session has reached the
                    # desired transaction size, commit them. 
                    if len(self.measurements_to_save) >= self.num_measurements_per_transaction:
                        self.commit()

                except Empty:
                    # If queue.get() times out, i.e. no new measurements came in 
                    # during the timeout period, commit what's currently in the 
                    # session
                    if len(self.measurements_to_save) > 0:
                        self.commit()

        except Exception as err:
            logging.error(f"Error in ScalarSaveThread: {err}")

        finally:
            pass # self.sa_session.close()


class UpdateScalarsSavedStatusThread(Thread):
    def __init__(self, 
                 queue: Queue,
                 data_uploader: DataUploader,
                 **kwargs
                ):
        self.queue = queue
        self.data_uploader = data_uploader

        super().__init__(**kwargs)

    def run(self):
        while True:
            measurements = self.queue.get()
            self.update(measurements)

    
    def update(self, measurement_or_measurements: Measurement | Iterable[Measurement]):
        """ Update ScalarsSavedTrackers associated with the shots and variables 
            in the measurement or measurements

        Parameters
        ----------
        measurements : Measurement | Iterable[Measurement]
            Single measurement or list of measurements whose shot/variable 
            combination mark as ScalarSaveStatus.Saved. 
        """
        def update_one(measurement: Measurement):
            if not isinstance(measurement, Measurement):
                raise TypeError(f"Object of type {type(measurement)} instead of Measurement found in UpdateScalarsSavedStatusThread queue.")

            # burst is not necessarily the current burst (could still be handling
            # scalars from a previous burst) so get it from the shot.
            burst: Burst = measurement.shot.burst
            burst.scalars_saved_tracker.update(measurement.variable, measurement.shot)

        if isinstance(measurement_or_measurements, Iterable):
            for measurement in measurement_or_measurements:
                update_one(measurement)
        else:  # scalar Measurement
            update_one(measurement_or_measurements)

        self.update_scalars_ready_pvs()

    def update_scalars_ready_pvs(self):
        """ Write timestamp of shot for which all scalars are ready to PVs

        Check what the most recent shot is for which all scalars - and all scalars 
        for all previous shots in the burst - are ready i.e. available in database, 
        and write this shot's timestamp to the associated PV. 

        There are PVs for fetched, monitored, image_backend, and "all" scalars. 

        """
        for pv_alias, variable_source in [('fetched_scalars_ready', VariableSource.fetch), 
                                          ('monitored_scalars_ready', VariableSource.monitor), 
                                          ('image_backend_scalars_ready', VariableSource.image_backend), 
                                          ('all_scalars_ready', None),  # None in ScalarsSavedTracker.highest_seq_all_scalars_ready defaults to all variable sources
                                         ]:
            
            highest_seq_all_scalars_ready = self.data_uploader.burst.scalars_saved_tracker.highest_seq_all_scalars_ready(variable_source)
            if highest_seq_all_scalars_ready > 0:
                shot_timestamp = self.data_uploader.burst.shot_directory[highest_seq_all_scalars_ready].timestamp
                self.data_uploader.burst_pvs[pv_alias].put(shot_timestamp.strftime("%Y-%m-%d %H:%M:%S.%fZ"))
                if variable_source is None:  # all variable sources
                    logging.info(f"All scalars for shots up to shot {highest_seq_all_scalars_ready} "
                                 f"({shot_timestamp.strftime('%Y-%m-%d %H:%M:%S.%fZ')}) ready."
                                ) 
            else:
                self.data_uploader.burst_pvs[pv_alias].put("")
                # logging.info(f"No shots have all scalars ready.")

class DataUploader:
    """ An app that monitors image and scalar PVs and handles them

    """
    def __init__(self):

        # Current burst, session, and scan information
        self.session = Session(timestamp=datetime.now(tz=UTC), title="default", description="This session is used if UI SessionID is not yet set.")
        self.scan = Scan(timestamp=datetime.now(tz=UTC), session=self.session, title="default", seq=0, notes="This scan is used if no Scan is known.")
        self.burst = Burst(timestamp=datetime.now(tz=UTC), repetition_rate=None, number_of_shots=None, seq=0)

        # disconnected, idle, preparing, armed, running
        self.burst_status: BurstStatus = BurstStatus.Disconnected
        self.scan.current_burst_seq = 1

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
        # self.requests_session = requests.Session()

        # will hold pvAccess subscriptions (Channel Access subscriptions are held 
        # in epics._PVmonitors_ )
        self.subscriptions: dict[PVName, P4PSubscription] = {}

        # whether to run callbacks. mainly to prevent callbacks from running when 
        # they are called while setting up monitors.
        self.enable_callbacks: bool = False

        # image upload queue
        self.image_upload_queue: Queue[ImageUploadData] = Queue()
        self.image_upload_thread = ImageUploadThread(self.image_upload_queue, env['IMAGE_BACKEND_ENDPOINT_URL'])
        self.image_collector = ImageCollector(self.image_upload_thread, instrument_device_map=INSTRUMENT_DEVICE_MAP)

        # scalars saved tracker queue
        self.update_scalars_saved_queue: Queue[Measurement | Iterable[Measurement]] = Queue()
        # and thread that updates the tracker and posts to PVs
        self.update_scalars_saved_thread = UpdateScalarsSavedStatusThread(self.update_scalars_saved_queue, self)

        # scalar upload queue
        self.scalar_save_queue: Queue[Measurement | Iterable[Measurement]] = Queue()
        self.scalar_save_thread = ScalarSaveThread(self.scalar_save_queue, update_scalars_saved_tracker_queue=self.update_scalars_saved_queue)

        # thread lock to prevent multiple threads creating the same shot.
        self.new_shot_lock = Lock()

        logging.info(f"DataUploader ready to run.")

    def run(self) -> None:
        """ Start monitors and listen forever.
        """

        # don't run callback code when they are called during monitor setup
        self.enable_callbacks = False

        # Load scalars and image devices from measurement database
        self.load_scalar_pv_list()
        self.load_image_pv_list()

        self.subscribe_to_burst_pvs()

        # subscribe to PVs in IOCs
        self.subscribe_to_image_pvs()
        self.subscribe_to_scalar_pvs()

        self.subscribe_to_last_analyzed_shot_id_pvs()

        # start image and scalar uploaders
        self.image_upload_thread.start()
        self.scalar_save_thread.start()
        self.update_scalars_saved_thread.start()

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

        # unsubscribe to fetch trigger PV
        try:
            self.subscriptions[self.fetch_trigger_variable.name].close()
        except (KeyError, AttributeError):
            logging.warning("No fetch trigger PV subscription to close.")

        # unsubscribe to last analyzed shot id PVs
        for image_device in self.image_devices:
            if hasattr(image_device, 'last_analyzed_shot_id_pva_monitor') and image_device.last_analyzed_shot_id_pva_monitor is not None:
                image_device.last_analyzed_shot_id_pva_monitor.close()
                logging.info(f"Closed PVAccess subscription for {image_device.last_analyzed_shot_id_pv_name}")

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
                # pull the value of the pv, otherwise it will be None, and PV.info chokes.
                variable.pv.get()

            elif variable.source == VariableSource.image_backend:
                # these don't have associated PVs
                variable.pv = None

            if variable.source == VariableSource.image_backend:
                # image_backend variables don't have associated PVs
                variable.info = {}
                variable.dtype = float
                continue

            # get cainfo for the variable
            variable.info = {}
            try:
                info: str | None = variable.pv.info
                if info is not None:
                    variable.info = parse_cainfo(info)
                    variable.dtype = parse_dtype(variable.info['type'])
                    logging.info(f"Got cainfo for {variable.name}")
                else:
                    variable.dtype = None
                    logging.warning(f"Unable to get cainfo for {variable.name}")
            except Exception as err:
                variable.dtype = None
                logging.error(f"Error getting cainfo for {variable.name}: {err}")

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
        def image_pv_is_available_over_pva(image_device: ImageDevice) -> bool:
            try:
                _ = pva.get(image_device.image_pv_name)
                return True
            except TimeoutError:
                return False

        def image_pv_is_available_over_ca(image_device: ImageDevice) -> bool:
            return (caget(image_device.image_pv_name) is not None)

        for image_device in self.image_devices:
            if image_pv_is_available_over_pva(image_device):            
                image_device.pva_monitor = \
                    pva.monitor(image_device.image_pv_name, partial(self.image_pv_callback, image_device))
                logging.info(f"Monitoring {image_device.image_pv_name} over pvAccess")
                
            elif image_pv_is_available_over_ca(image_device):
                image_device.pv = PV(image_device.image_pv_name, callback=partial(self.image_pv_callback_ca, image_device))
                logging.info(f"Monitoring {image_device.image_pv_name} over Channel Access")

            else:
                logging.warning(f"Image PV {image_device.image_pv_name} not available over pvAccess or Channel Access.")

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
                ('scan_title', [self.scan_title_monitor_callback]),
                ('scan_number', [self.scan_number_monitor_callback]),

                ('session_timestamp', [self.session_timestamp_monitor_callback]),
                ('scan_timestamp', [self.scan_timestamp_monitor_callback]),
                ('burst_timestamp', []),
            ]:

            self.burst_pvs[pv_alias] = PV(PV_NAMES[pv_alias], callback=callbacks, )
            logging.info(f"Montitoring {PV_NAMES[pv_alias]} over Channel Access.")

        # PV connections without monitoring
        for pv_alias in ['fetched_scalars_ready', 
                         'monitored_scalars_ready', 
                         'image_backend_scalars_ready', 
                         'all_scalars_ready', 
                        ]:
            self.burst_pvs[pv_alias] = PV(PV_NAMES[pv_alias], auto_monitor=False)

    def subscribe_to_last_analyzed_shot_id_pvs(self) -> None:
        """_summary_
        """
        for image_device in self.image_devices:

            if image_device.name not in LAST_ANALYZED_SHOT_ID_PV_NAMES:
                continue

            image_device.last_analyzed_shot_id_pv_name = LAST_ANALYZED_SHOT_ID_PV_NAMES[image_device.name]

            image_device.last_analyzed_shot_id_pv = \
                PV(image_device.last_analyzed_shot_id_pv_name + '.$', callback=partial(self.image_analysis_complete_callback, image_device))
            logging.info(f"Monitoring {image_device.last_analyzed_shot_id_pv_name} over Channel Access")


    def fetch_trigger_pv_monitor_callback(self, value: NTBase) -> None:
        """
        """
        if not self.enable_callbacks:
            return

        try:
            variables_to_fetch = [variable for variable in self.variables
                                  if variable.source == VariableSource.fetch
                                     and variable.pv.connected 
                                     and (variable.dtype is not None) and issubclass(variable.dtype, Number)
                                 ]

            shot_seq = ShotSeq(self.fetch_trigger_variable.counter + 1)

            # create shot if it doesn't exist
            if shot_seq not in self.burst.shot_directory:
                self.create_new_shot(shot_seq)

            # then grab it from directory
            shot = self.burst.shot_directory[shot_seq]

            # fetch values
            values = [variable.pv.get() for variable in variables_to_fetch]

            for variable, value in zip(variables_to_fetch, values):
                if value is None:
                    logging.warning(f"No value for {variable.name}. Possibly it went offline.")
                    self.burst.scalars_saved_tracker.update(variable, shot, ScalarSaveStatus.Error)
                    continue
                self.scalar_save_queue.put(Measurement(variable=variable, shot=shot, value=float(value)))

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

        if self.burst_status == BurstStatus.Preparing:
            assert previous_status != BurstStatus.Preparing
            self.prepare_burst()

        # when burst ends, spit out variable counts
        if previous_status == BurstStatus.Running and self.burst_status == BurstStatus.Idle:
            logging.info(f"Handled {self.fetch_trigger_variable.counter:d} updates of fetch tigger pv {self.fetch_trigger_variable.name} during burst.")
            for variable in self.variables:
                if variable.source == VariableSource.monitor:
                    logging.info(f"Handled {variable.counter:d} updates of monitored {variable.name} during burst.")
            for image_device in self.image_devices:
                logging.info(f"Handled {image_device.counter:d} updates of image device {image_device.name} during burst.")

    def prepare_burst(self) -> None:
        """ 
        """
        try:
            pva.put("TakeNShots:BurstInDB", 0)

            self.burst = Burst(timestamp=self.datetime_from_pv_string(self.burst_pvs['burst_timestamp'].get()),
                               scan=self.scan, 
                               seq=self.scan.current_burst_seq,
                               number_of_shots=self.burst_pvs['burst_num_shots'].value,
                               repetition_rate=self.burst_pvs['burst_frequency'].value,
                              )

            logging.info(f"New Burst {self.burst.timestamp:%Y-%m-%d %H:%M:%S.%f}, number {self.burst.seq:d}, with frequency = {self.burst.repetition_rate:.3f} Hz and NumShots = {self.burst.number_of_shots:d}")

            with SQLAlchemySession() as sa_session:
                sa_session.add(self.burst)
                sa_session.commit()

            self.reset_counters()
            self.scan.current_burst_seq += 1

            # create map of shot sequence to shot object
            self.burst.shot_directory = {}

            # Scalars Saved Tracker
            variables_to_track = [variable for variable in self.variables if (
                # varible is connected to its PV through the pyepics pv.PV class
                (((variable.pv is not None) and variable.pv.connected)
                 or (variable.source == VariableSource.image_backend)  # does not have an associated PV
                )
                # Currently, I'm not fetching non-numeric variables. 
                and (variable.dtype is not None) and issubclass(variable.dtype, Number)
            )]
            self.burst.scalars_saved_tracker = ScalarsSavedTracker(variables_to_track)

            # Finally, notify system that scalar database is ready for this Burst
            pva.put("TakeNShots:BurstInDB", 1)

        except Exception as err:
            logging.error(f"Unable to create burst: {err}")


    def create_new_shot(self, shot_seq: ShotSeq):
        """ Thread-safe creation of new Shot in Burst

        Using a lock is necessary because several callbacks - i.e. threads - 
        check if a shot exists, and if not create it and add it to the burst
        shot_directory.

        Parameters
        ----------
        seq : ShotSeq

        """
        with self.new_shot_lock:
            if shot_seq in self.burst.shot_directory:
                return

            self.burst.shot_directory[shot_seq] = Shot(
                timestamp=self.burst.timestamp + timedelta(seconds=(shot_seq - 1) / self.burst.repetition_rate), 
                burst=self.burst, 
                seq=shot_seq,
            )


    def session_timestamp_monitor_callback(self, value: str, **kwargs):
        self.session = Session(title=self.session.title, timestamp=self.datetime_from_pv_string(value))
        logging.info(f"New session {self.session.timestamp} with title \"{self.session.title}\"")

    def session_title_monitor_callback(self, value: str, **kwargs):
        self.session.title = value
        logging.info(f"Set session title to \"{self.session.title}\"")


    def scan_timestamp_monitor_callback(self, value: str, **kwargs):
        self.scan = Scan(timestamp=self.datetime_from_pv_string(value), title=self.scan.title, seq=self.scan.seq, session=self.session)
        logging.info(f"New scan {self.scan.timestamp}, number {self.scan.seq} with title \"{self.scan.title}\"")
        self.scan.current_burst_seq = 1

    def scan_number_monitor_callback(self, value: int, **kwargs):
        self.scan.seq = value
        logging.info(f"Scan number set to \"{self.scan.seq}\"")

    def scan_title_monitor_callback(self, value: NDArray, **kwargs):
        """ Decode byte array and set scan.title

        The scan title PV is of waveform type (to accommodate long strings), which 
        appears as an np.ndarray of dtype int representing ascii characters. 
        
        """
        self.scan.title = ''.join(map(chr, value))
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
            shot_seq = ShotSeq(image_device.counter + 1)

            if shot_seq not in self.burst.shot_directory:
                self.create_new_shot(shot_seq)
            shot = self.burst.shot_directory[shot_seq]

            # determine shot id
            shot_id = f"burst-{self.burst.timestamp:%Y-%m-%dT%H-%M-%S-%fZ}/shot-{shot.timestamp:%Y-%m-%dT%H-%M-%S-%fZ}"

            # put image data in queue to be uploaded to image endpoint
            self.image_collector.put(ImageUploadData(
                device_name = image_device.name,
                shot_id = shot_id,
                image_data = image_data,
            ))

        except Exception as err:
            image_device_name = getattr(image_device, 'name', "device with no 'name' attribute")
            logging.error(f"Error in image_pv_callback for {image_device_name}: {err}")

        finally:
            # increase shot counter
            image_device.counter += 1

    def image_pv_callback_ca(self, image_device: ImageDevice, value: NDArray, **kwargs) -> None:
        """ Callback for image PVs over Channel Access

        Adapter to call image_pv_callback with the correct arguments.
        """
        self.image_pv_callback(image_device, image_data=value)

    def scalar_pv_callback(self, variable: Variable, value: float, **kwargs) -> None:
        """ TODO
        """
        if not self.enable_callbacks:
            return

        try:
            shot_seq = ShotSeq(variable.counter + 1)

            # create new Shot if this shot_seq is new
            if shot_seq not in self.burst.shot_directory:
                self.create_new_shot(shot_seq)
            shot = self.burst.shot_directory[shot_seq]

            self.scalar_save_queue.put(Measurement(
                variable = variable,
                shot = shot,
                value = value,
            ))

        except Exception as err:
            variable_name = getattr(variable, 'name', "variable with no 'name' attribute")
            logging.error(f"Error in scalar_pv_callback for {variable_name}: {err}")

            try:
                self.burst.scalars_saved_tracker.update(variable, shot, ScalarSaveStatus.Error)
            except Exception as scalars_saved_tracker_update_error:
                logging.error(f"Error updating scalars_saved_tracker for {variable_name}: {scalars_saved_tracker_update_error}")

        finally:
            # increase shot counter
            variable.counter += 1

    def image_analysis_complete_callback(self, device: ImageDevice, value: NDArray, **kwargs) -> None:
        """ Callback for last_analyzed_shot_id PV 
        
        Parameters
        ----------
        value : str
            Shot ID string             
        """
        if (not self.enable_callbacks) or (len(value) == 0):
            return

        # value is a byte array; convert to string and drop the null character at the end
        shot_id_str = ''.join(map(chr, value))[:-1]

        # derive shot number from shot_id string
        burst_datetime, shot_datetime = parse_shot_id(shot_id_str)
        shot_seq = ShotSeq((shot_datetime - burst_datetime).total_seconds() * self.burst.repetition_rate + 1)

        # create shot if it doesn't exist
        if shot_seq not in self.burst.shot_directory:
            self.create_new_shot(shot_seq)

        # then grab it from directory
        shot = self.burst.shot_directory[shot_seq]

        # make sure the shot timestamp matches the shot_id_str timestamp
        assert abs((shot.timestamp - shot_datetime).total_seconds()) < 1e-5, \
            f"Shot timestamp in burst's shot directory for shot {shot_seq} ({shot.timestamp}) does not match shot_id_str timestamp {shot_id_str} for device {device.name}"

        # update scalars tracker for all image_backend variables associated with 
        # this device 
        self.update_scalars_saved_queue.put(
            [Measurement(variable=variable, shot=shot) 
             for variable in self.variables 
             if variable.source == VariableSource.image_backend 
                 and variable.name.startswith(device.name)
            ]
        )

    def datetime_from_pv_string(self, datetime_str: str) -> datetime:
        """ Turn string obtained from session, scan, or burst timestamp PV into datetime

        Assumes %Y-%m-%d %H:%M:%S.%f format, in UTC.

        Parameters
        ----------
        datetime_str : str

        Returns
        -------
        utc_datetime : datetime
            datetime with UTC timezone

        """
        try:
            return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%fZ").replace(tzinfo=UTC)
        except ValueError:
            logging.warning(f"Unable to parse datetime string {datetime_str}. Returning current time.")
            return datetime.now(tz=UTC)

