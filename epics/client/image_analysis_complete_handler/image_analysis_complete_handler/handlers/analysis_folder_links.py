from __future__ import annotations

from os.path import relpath
import re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
LOCAL_TIMEZONE = ZoneInfo("US/Central")
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..utils.types import ImageAnalysisCompleteData
    from measurement_db.orm.tables import Session, Scan, Burst
from .base import ImageAnalysisCompleteHandler
from ..utils.env import get_env
env = get_env()

from measurement_db.orm.tables import Shot
from measurement_db.utils import get_sqlalchemy_engine
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy import select

class CreateAnalysisFolderLinks(ImageAnalysisCompleteHandler):
    """ Creates a human-friendly link to the shot folder
    """

    SHOTS_HANDLED_SET_MAX_SIZE = 12000
    SHOTS_HANDLES_SET_PURGE_TO = 10000

    def __init__(self, base_path: str | Path):
        self.data_storage_base_path = Path(base_path)

        self.shots_handled = set()
        self.sqlalchemy_engine = get_sqlalchemy_engine()

        super().__init__()

    def generate_analysis_folder(self, shot_timestamp: datetime) -> Path:
        with SQLAlchemySession(self.sqlalchemy_engine) as sa_session:
            shot = sa_session.scalar(select(Shot).where(Shot.timestamp == shot_timestamp))

            burst: Burst = shot.burst
            scan: Scan = burst.scan
            session: Session = scan.session

        # make sure that this timestamp either has no timezone info or it's utc.
        assert session.timestamp.tzinfo is None or session.timestamp.tzname().lower() == 'utc'
        session_timestamp_local = session.timestamp.replace(tzinfo=ZoneInfo("UTC")).astimezone(LOCAL_TIMEZONE)
        year_folder_name = f"{session_timestamp_local:%Y}"
        session_folder_name = f"Session-{session_timestamp_local:%Y-%m-%d-%H-%M-%S%Z}"
        # for scan folder name, take the scan description and replace invalid characters
        # with dash, and spaces with underscore, then truncate to 80 characters
        scan_folder_name = re.sub(r"[\\/:\"*?<>|]", '-', scan.description)
        scan_folder_name = re.sub(r"\s", '_', scan_folder_name)
        scan_folder_name = scan_folder_name[:80]
        # make sure the name starts with the format Scan-012
        assert re.match("^Scan-\d{3}", scan_folder_name) is not None

        burst_folder_name = f"Burst-{burst.seq:04d}"
        shot_folder_name = f"Shot-{shot.seq:05d}"

        analysis_folder = Path(self.data_storage_base_path, "analysis", 
                               year_folder_name, session_folder_name, scan_folder_name, 
                               burst_folder_name, shot_folder_name
                          ) 

        return analysis_folder


    def handle(self, message_data: ImageAnalysisCompleteData) -> None:
        if message_data['shot_id'] in self.shots_handled:
            return

        # expecting a shot_id in the format burst-2024-01-02T03-04-05-678901Z/shot-2024-01-02T03-04-05-678901Z
        # function copied from image-processing-backend/applications/rq_worker/src/result_handlers/db.py
        def parse_shot_id(shot_id: str) -> tuple[datetime, datetime]:
            burst_str, shot_str = shot_id.split('/')
            burst_datetime = datetime.strptime(burst_str, "burst-%Y-%m-%dT%H-%M-%S-%f%z")  # the %z will pick up the Z as utc
            shot_datetime = datetime.strptime(shot_str, "shot-%Y-%m-%dT%H-%M-%S-%f%z")
            return burst_datetime, shot_datetime

        _, shot_datetime = parse_shot_id(message_data['shot_id'])

        shot_folder = self.data_storage_base_path / "data" / message_data['shot_id']
        analysis_folder = self.generate_analysis_folder(shot_datetime)

        analysis_folder.parent.mkdir(parents=True, exist_ok=True)
        analysis_folder.symlink_to(relpath(shot_folder, analysis_folder.parent))

        # prevent this link from being created again by adding it to a seen set.
        self.shots_handled.add(message_data['shot_id'])
        # remove older items from seen set
        if len(self.shots_handled) > self.SHOTS_HANDLED_SET_MAX_SIZE:
            self.purge_shots_handled_set()

    def purge_shots_handled_set(self):
        self.shots_handled = set(sorted(self.shots_handled)[:self.SHOTS_HANDLES_SET_PURGE_TO])
