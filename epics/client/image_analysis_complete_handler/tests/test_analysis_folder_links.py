from __future__ import annotations
import unittest
import tempfile
from pathlib import Path

from utils.types import ImageAnalysisCompleteMessage
from handlers.analysis_folder_links import CreateAnalysisFolderLinks

from measurement_db.utils import get_sqlalchemy_engine
from measurement_db.orm.tables import Shot
from sqlalchemy import select, func
from sqlalchemy.orm import Session as SQLAlchemySession

class TestAnalysisFolderLinks(unittest.TestCase):
    def setUp(self) -> None:
        self.data_base_temp_dir = tempfile.TemporaryDirectory()
        self.data_base_path = Path(self.data_base_temp_dir.name)
        (self.data_base_path / "data").mkdir()
        (self.data_base_path / "analysis").mkdir()

        # pick one shot to create a data folder for
        with SQLAlchemySession(get_sqlalchemy_engine()) as sa_session:
            self.shot: Shot = sa_session.scalar(select(func.max(Shot)))

        self.shot_id = (
            f"burst-{self.shot.burst.timestamp:%Y-%m-%dT%H-%M-%S-%fZ}/" 
            f"shot-{self.shot.timestamp:%Y-%m-%dT%H-%M-%S-%fZ}"
        )

        (self.data_base_path / "data" / self.shot_id).mkdir(parents=True) 

        return super().setUp()
    
    def test_create_link(self) -> None:
        message = ImageAnalysisCompleteMessage(
            device_name="test",
            shot_id = self.shot_id
        )

        handler = CreateAnalysisFolderLinks()
        handler.handle(message)

    def tearDown(self) -> None:
        self.data_base_temp_dir.cleanup()
        
        return super().tearDown()


if __name__ == "__main__":
    unittest.main()