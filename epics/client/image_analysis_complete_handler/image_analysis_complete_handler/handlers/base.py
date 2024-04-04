from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..utils.types import ImageAnalysisCompleteData

class ImageAnalysisCompleteHandler:
    """ Base class for handlers.
    """
    def __init__(self):
        pass

    def handle(self, message: ImageAnalysisCompleteData) -> None:
        raise NotImplementedError("handle() method should be implemented by derived class.")
    
