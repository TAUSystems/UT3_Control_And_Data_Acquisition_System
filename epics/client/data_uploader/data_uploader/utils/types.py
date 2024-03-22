from __future__ import annotations

from typing import TypedDict, NamedTuple, NewType
from enum import Enum

class ImageAnalysisFinishedMessage(TypedDict):
    device_name: str
    shot_id: str
    num_images: int
    num_arrays: int
    num_scalars: int
    errors: list[str]

class ImageDeviceDirectoryEntry(NamedTuple):
    image_pv_name: str
    array_counter_pv_name: str
    last_analyzed_pv_name: str

DeviceName = NewType("DeviceName", str)
PVName = NewType("PVName", str)

class BurstStatus(Enum):
    Disconnected = 0
    Idle         = 1
    Preparing    = 2
    Armed        = 3
    Running      = 4
    Stop         = 5
