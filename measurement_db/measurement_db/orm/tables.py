import enum
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from sqlalchemy import Double, ForeignKey, DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass

class Variable(Base):
    __tablename__ = "variable"

    name: Mapped[str] = mapped_column(String(252), primary_key=True)
    id: Mapped[int] = mapped_column(autoincrement=True)
    description: Mapped[str] = mapped_column(String(252), default="")
    units: Mapped[Optional[str]] = mapped_column(String(16))
    display_units: Mapped[Optional[str]] = mapped_column(String(16))
    display_unit_multiplier: Mapped[Optional[float]] = mapped_column(Double)

class ImageDevice(Base):
    __tablename__ = "image_device"

    name: Mapped[str] = mapped_column(String(252), primary_key=True)
    image_pv_name: Mapped[str] = mapped_column(String(252))

class Session(Base):
    __tablename__ = "session"

    timestamp: Mapped[datetime] = mapped_column(DateTime(), primary_key=True, default=func.current_timestamp())
    title: Mapped[str] = mapped_column(String(252), default="")
    description: Mapped[str] = mapped_column(Text(), default="")

    operator: Mapped[str] = mapped_column(String(252), default="", doc="Name of the person or organization operating this session.")

class Scan(Base):
    __tablename__ = "scan"

    timestamp: Mapped[datetime] = mapped_column(DateTime(), primary_key=True, default=func.current_timestamp())
    session: Mapped[datetime] = mapped_column(ForeignKey('session.timestamp'))
    number: Mapped[int] = mapped_column(index=True, doc="Sequence number of this scan within session")

    description: Mapped[str] = mapped_column(Text(), default="")

    notes: Mapped[str] = mapped_column(Text(), default="")


class Burst(Base):
    __tablename__ = "burst"

    timestamp: Mapped[datetime] = mapped_column(DateTime(), primary_key=True)
    scan: Mapped[datetime] = mapped_column(ForeignKey('scan.timestamp'))
    seq: Mapped[int] = mapped_column(doc="Sequence number of this burst within scan")

    number_of_shots: Mapped[int]
    repetition_rate: Mapped[float] = mapped_column(Double, doc="Repetition rate in Hertz")

class Shot(Base):
    __tablename__ = "shot"

    timestamp: Mapped[datetime] = mapped_column(DateTime(), primary_key=True)
    burst: Mapped[datetime] = mapped_column(ForeignKey('burst.timestamp'))
    seq: Mapped[int] = mapped_column(doc="Sequence number of this shot within burst")

class Measurement(Base):
    __tablename__ = "measurement"

    shot: Mapped[datetime] = mapped_column(ForeignKey('shot.timestamp'), primary_key=True)
    variable_id: Mapped[int] = mapped_column(ForeignKey('variable.id'), primary_key=True)
    value: Mapped[float] = mapped_column(Double)
