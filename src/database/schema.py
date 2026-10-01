"""
SQLAlchemy 2.0 Relational Database Schema for Genealogy System.
GEDCOM compliant, high performance, with indexes for JDN dates, FTS, and UUID keys.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional

from sqlalchemy import (
    Column, String, Integer, Float, Text, Enum as SQLEnum,
    ForeignKey, DateTime, Index, Table
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.core.enums import (
    Sex, NameType, UnionType, ParentChildRelType, SpouseRole,
    EventType, EventRole, DateModifier, SourceQuality
)


class Base(DeclarativeBase):
    pass


class PersonModel(Base):
    __tablename__ = "persons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sex: Mapped[Sex] = mapped_column(SQLEnum(Sex), default=Sex.UNKNOWN, nullable=False)
    primary_name_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    names: Mapped[List["PersonNameModel"]] = relationship(
        "PersonNameModel", back_populates="person", cascade="all, delete-orphan", foreign_keys="PersonNameModel.person_id"
    )
    events: Mapped[List["EventModel"]] = relationship(
        "EventModel", back_populates="person", cascade="all, delete-orphan", foreign_keys="EventModel.person_id"
    )
    family_as_child: Mapped[List["FamilyChildModel"]] = relationship(
        "FamilyChildModel", back_populates="person", cascade="all, delete-orphan"
    )
    family_as_spouse: Mapped[List["FamilySpouseModel"]] = relationship(
        "FamilySpouseModel", back_populates="person", cascade="all, delete-orphan"
    )
    media: Mapped[List["MediaModel"]] = relationship(
        "MediaModel", back_populates="person"
    )
    attributes: Mapped[List["PersonAttributeModel"]] = relationship(
        "PersonAttributeModel", back_populates="person", cascade="all, delete-orphan"
    )


class PersonAttributeModel(Base):
    __tablename__ = "person_attributes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id: Mapped[str] = mapped_column(String(36), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    tag: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    attribute_key: Mapped[str] = mapped_column(String(128), nullable=False)
    attribute_value: Mapped[str] = mapped_column(Text, nullable=False)

    person: Mapped["PersonModel"] = relationship("PersonModel", back_populates="attributes")


class PersonNameModel(Base):
    __tablename__ = "person_names"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id: Mapped[str] = mapped_column(String(36), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    name_type: Mapped[NameType] = mapped_column(SQLEnum(NameType), default=NameType.BIRTH, nullable=False)
    surname: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    given_names: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    prefix: Mapped[Optional[str]] = mapped_column(String(32))
    suffix: Mapped[Optional[str]] = mapped_column(String(32))
    surname_soundex: Mapped[Optional[str]] = mapped_column(String(16), index=True)

    person: Mapped["PersonModel"] = relationship("PersonModel", back_populates="names", foreign_keys=[person_id])


class FamilyModel(Base):
    __tablename__ = "families"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    union_type: Mapped[UnionType] = mapped_column(SQLEnum(UnionType), default=UnionType.MARRIAGE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    spouses: Mapped[List["FamilySpouseModel"]] = relationship(
        "FamilySpouseModel", back_populates="family", cascade="all, delete-orphan"
    )
    children: Mapped[List["FamilyChildModel"]] = relationship(
        "FamilyChildModel", back_populates="family", cascade="all, delete-orphan"
    )
    events: Mapped[List["EventModel"]] = relationship(
        "EventModel", back_populates="family", cascade="all, delete-orphan"
    )


class FamilySpouseModel(Base):
    __tablename__ = "family_spouses"

    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id", ondelete="CASCADE"), primary_key=True)
    person_id: Mapped[str] = mapped_column(String(36), ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[SpouseRole] = mapped_column(SQLEnum(SpouseRole), default=SpouseRole.PARTNER, nullable=False)

    family: Mapped["FamilyModel"] = relationship("FamilyModel", back_populates="spouses")
    person: Mapped["PersonModel"] = relationship("PersonModel", back_populates="family_as_spouse")


class FamilyChildModel(Base):
    __tablename__ = "family_children"

    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id", ondelete="CASCADE"), primary_key=True)
    person_id: Mapped[str] = mapped_column(String(36), ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True)
    rel_type: Mapped[ParentChildRelType] = mapped_column(SQLEnum(ParentChildRelType), default=ParentChildRelType.BIOLOGICAL, nullable=False)

    family: Mapped["FamilyModel"] = relationship("FamilyModel", back_populates="children")
    person: Mapped["PersonModel"] = relationship("PersonModel", back_populates="family_as_child")


class PlaceModel(Base):
    __tablename__ = "places"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    hierarchy: Mapped[Optional[str]] = mapped_column(String(256))  # e.g., "Polska, Mazowieckie, Warszawa"
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type: Mapped[EventType] = mapped_column(SQLEnum(EventType), nullable=False)
    date_raw: Mapped[Optional[str]] = mapped_column(String(128))
    date_modifier: Mapped[DateModifier] = mapped_column(SQLEnum(DateModifier), default=DateModifier.EXACT)
    jdn_min: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    jdn_max: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    person_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("persons.id", ondelete="CASCADE"))
    family_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("families.id", ondelete="CASCADE"))
    place_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("places.id"))

    person: Mapped[Optional["PersonModel"]] = relationship("PersonModel", back_populates="events")
    family: Mapped[Optional["FamilyModel"]] = relationship("FamilyModel", back_populates="events")
    place: Mapped[Optional["PlaceModel"]] = relationship("PlaceModel")
    witnesses: Mapped[List["EventWitnessModel"]] = relationship("EventWitnessModel", back_populates="event", cascade="all, delete-orphan")


class EventWitnessModel(Base):
    __tablename__ = "event_witnesses"

    event_id: Mapped[str] = mapped_column(String(36), ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    person_id: Mapped[str] = mapped_column(String(36), ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[EventRole] = mapped_column(SQLEnum(EventRole), default=EventRole.WITNESS)

    event: Mapped["EventModel"] = relationship("EventModel", back_populates="witnesses")


class SourceModel(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(128))
    publication_info: Mapped[Optional[str]] = mapped_column(Text)
    repository_name: Mapped[Optional[str]] = mapped_column(String(128))
    quality: Mapped[SourceQuality] = mapped_column(SQLEnum(SourceQuality), default=SourceQuality.HIGH)


class CitationModel(Base):
    __tablename__ = "citations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    person_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("persons.id", ondelete="CASCADE"))
    event_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("events.id", ondelete="CASCADE"))
    page_reference: Mapped[Optional[str]] = mapped_column(String(128))
    confidence: Mapped[int] = mapped_column(Integer, default=3)
    text_quote: Mapped[Optional[str]] = mapped_column(Text)


class MediaModel(Base):
    __tablename__ = "media_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(128))
    mime_type: Mapped[Optional[str]] = mapped_column(String(64))
    person_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("persons.id", ondelete="CASCADE"))

    person: Mapped[Optional["PersonModel"]] = relationship("PersonModel", back_populates="media")


class ChangeLogModel(Base):
    __tablename__ = "change_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operation_id: Mapped[str] = mapped_column(String(36), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(16))  # CREATE, UPDATE, DELETE
    delta_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
