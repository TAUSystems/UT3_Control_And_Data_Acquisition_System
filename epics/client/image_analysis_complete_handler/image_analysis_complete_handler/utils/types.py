from __future__ import annotations

from typing import TypedDict, NamedTuple, NewType

class ImageAnalysisCompleteData(TypedDict):
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