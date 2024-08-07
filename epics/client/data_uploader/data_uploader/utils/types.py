from __future__ import annotations

from typing import TypedDict, NamedTuple, NewType, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from measurement_db.orm.tables import Variable, Shot

DeviceName = NewType("DeviceName", str)
InstrumentName = NewType("InstrumentName", str)
ShotId = NewType("ShotId", str)
PVName = NewType("PVName", str)

class ImageAnalysisFinishedMessage(TypedDict):
    device_name: DeviceName
    shot_id: ShotId
    num_images: int
    num_arrays: int
    num_scalars: int
    errors: list[str]

class ImageDeviceDirectoryEntry(NamedTuple):
    image_pv_name: str
    array_counter_pv_name: str
    last_analyzed_pv_name: str

class BurstStatus(Enum):
    Disconnected = 0
    Idle         = 1
    Preparing    = 2
    Armed        = 3
    Running      = 4

class ScalarSaveStatus(Enum):
    """ Status of a scalar being saved to the measurement database
    """
    # Scalar has not yet been saved to measurement db
    Waiting = 0
    # Scalar has been saved to measurement db
    Saved = 1
    # Not expecting scalar to come in, perhaps because it disconnected
    NotExpecting = 2
    # Failed to save scalar to db
    Error = 3
    # Did not get request to save scalar, long after it was expected
    TimedOut = 4

# a one-indexed sequence number of a shot within a burst
ShotSeq = NewType("ShotSeq", int)

# Represents the bytestream of a TIFF-formatted image
TiffBytes = NewType("TiffBytes", bytes)
