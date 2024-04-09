from __future__ import annotations
from pathlib import Path
from datetime import datetime, timedelta, timezone
from random import random

from measurement_db.orm.tables import Session, Scan, Burst, Shot, Measurement, Variable, ImageDevice
from measurement_db.utils import get_sqlalchemy_engine

from sqlalchemy.orm import Session as SASession
from sqlalchemy import select

sa_engine = get_sqlalchemy_engine()

# add some measurements
session = Session(title='test_session', description="Test session.", timestamp=datetime.now(tz=timezone.utc))
scan = Scan(session=session, seq=1, description="Scan-001", timestamp=datetime.now(tz=timezone.utc))
now = datetime.now(tz=timezone.utc)
bursts = []
shots = []
measurements = []

with SASession(sa_engine) as sa_session:

    variables = sa_session.scalars(select(Variable))

    for burst_seq in range(1, 3+1):
        burst_timestamp = now + timedelta(seconds=4 * burst_seq)
        burst_num_shots = 3
        burst = Burst(scan=scan, timestamp=burst_timestamp, seq=burst_seq, number_of_shots=burst_num_shots, repetition_rate=1.0)
        bursts.append(burst)
        
        for seq in range(1, burst_num_shots + 1):
            shot = Shot(burst=burst, timestamp=burst_timestamp + timedelta(seconds=1.0 * seq), seq=seq)
            shots.append(shot)
            for variable in variables:
                measurements.append(Measurement(shot=shot, variable=variable, value=random()))


    sa_session.add(session)
    sa_session.add(scan)
    for burst in bursts:
        sa_session.add(burst)
    for shot in shots:
        sa_session.add(shot)
    for measurement in measurements:
        sa_session.add(measurement)
    
    sa_session.commit()

