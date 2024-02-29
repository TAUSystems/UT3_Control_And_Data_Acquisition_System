import enum
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from sqlalchemy import Double, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

with (Path(__file__).parent/"measurement_names.txt").open() as f:
    MeasurementName = enum.Enum('MeasurementName', [line.strip('\n') for line in f])

class Session(Base):
    __tablename__ = "session"

    timestamp: Mapped[datetime] = mapped_column(DateTime(), primary_key=True, default=func.current_timestamp())
    title: Mapped[Optional[str]]
    description: Mapped[Optional[str]]

    operator: Mapped[Optional[str]]

class Scan(Base):
    __tablename__ = "scan"

    timestamp: Mapped[datetime] = mapped_column(DateTime(), primary_key=True, default=func.current_timestamp())
    number: Mapped[int] = mapped_column(index=True)
    description: Mapped[Optional[str]]

    notes: Mapped[Optional[str]]


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
