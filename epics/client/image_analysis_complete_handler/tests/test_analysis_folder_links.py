from __future__ import annotations
import unittest
import tempfile
from pathlib import Path
import os

from image_analysis_complete_handler.utils.types import ImageAnalysisCompleteMessage
from image_analysis_complete_handler.handlers.analysis_folder_links import CreateAnalysisFolderLinks

from measurement_db.utils import get_sqlalchemy_engine
from measurement_db.orm.tables import Shot
from sqlalchemy import select, func
from sqlalchemy.orm import Session as SQLAlchemySession

class TestAnalysisFolderLinks(unittest.TestCase):
    def setUp(self) -> None:
        self.data_base_temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATA_DISK_STORAGE_BASE_DIRECTORY"] = self.data_base_temp_dir.name
        self.data_base_path = Path(self.data_base_temp_dir.name)
        (self.data_base_path / "data").mkdir()
        (self.data_base_path / "analysis").mkdir()

        # pick one shot to create a data folder for
        with SQLAlchemySession(get_sqlalchemy_engine()) as sa_session:
            self.shot: Shot = sa_session.scalar(
                select(Shot)
                .order_by(Shot.timestamp.desc())
                .limit(1)
            )
            self.burst = self.shot.burst

        self.shot_id = (
            f"burst-{self.burst.timestamp:%Y-%m-%dT%H-%M-%S-%fZ}/" 
            f"shot-{self.shot.timestamp:%Y-%m-%dT%H-%M-%S-%fZ}"
        )

        (self.data_base_path / "data" / self.shot_id).mkdir(parents=True)
        (self.data_base_path / "data" / self.shot_id / "scalars.dat").write_text("")

        return super().setUp()
    
    def test_create_link(self) -> None:
        message = ImageAnalysisCompleteMessage(
            device_name="test",
            shot_id = self.shot_id
        )

        handler = CreateAnalysisFolderLinks(self.data_base_path)
        handler.handle(message)

        # dive 5 levels deep into "analysis" folder, assuming there's only one
        # folder at each level.
        p = self.data_base_path / "analysis"
        for _ in range(5):
            p = next(p.iterdir())

        self.assertTrue((p / "scalars.dat").exists())

    def tearDown(self) -> None:
        self.data_base_temp_dir.cleanup()
        
        return super().tearDown()


if __name__ == "__main__":
    unittest.main()