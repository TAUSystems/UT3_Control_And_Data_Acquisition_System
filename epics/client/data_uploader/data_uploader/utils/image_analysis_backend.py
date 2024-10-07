from datetime import datetime

def parse_shot_id(shot_id: str) -> tuple[datetime, datetime]:
    burst_str, shot_str = shot_id.split('/')
    burst_datetime = datetime.strptime(burst_str, "burst-%Y-%m-%dT%H-%M-%S-%f%z").replace(tzinfo=None)  # the %z will pick up the Z as utc
    shot_datetime = datetime.strptime(shot_str, "shot-%Y-%m-%dT%H-%M-%S-%f%z").replace(tzinfo=None)
    return burst_datetime, shot_datetime

