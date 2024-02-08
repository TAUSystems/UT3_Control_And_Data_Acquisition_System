import enum
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from sqlalchemy import Double, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

with (Path(__file__).parent/"measurement_names.txt").open() as f:
    MeasurementName = enum.Enum('MeasurementName', [line.strip('\n') for line in f])

class Scan(Base):
    __tablename__ = "scan"

    timestamp: Mapped[datetime] = mapped_column(DateTime(), primary_key=True)
    description: Mapped[Optional[str]]

    # properties relating to being able to identify a particular Scan
    year: Mapped[int] = mapped_column(index=True)
    month: Mapped[int] = mapped_column(index=True)
    day: Mapped[int] = mapped_column(index=True)
    number: Mapped[int] = mapped_column(index=True)

class Burst(Base):
    __tablename__ = "burst"

    timestamp: Mapped[datetime] = mapped_column(DateTime(), primary_key=True)
    scan: Mapped[Optional[datetime]] = mapped_column(ForeignKey('scan.timestamp'))
    seq: Mapped[Optional[int]] = mapped_column(doc="Sequence number of this burst within scan")

class Shot(Base):
    __tablename__ = "shot"

    timestamp: Mapped[datetime] = mapped_column(DateTime(), primary_key=True)
    burst: Mapped[datetime] = mapped_column(ForeignKey('burst.timestamp'))
    seq: Mapped[int] = mapped_column(doc="Sequence number of this shot within burst")

class Measurement(Base):
    __tablename__ = "measurement"

    shot: Mapped[datetime] = mapped_column(ForeignKey('shot.timestamp'), primary_key=True)
    measurement_name: Mapped[MeasurementName] = mapped_column(primary_key=True)
    value: Mapped[float] = mapped_column(Double)
