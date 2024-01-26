from __future__ import annotations

from typing import TypedDict

class ImageAnalysisFinishedMessage(TypedDict):
    device_name: str
    shot_id: str
    num_images: int
    num_arrays: int
    num_scalars: int
    errors: list[str]
