"""
Unit tests for GIS Migration Engine, Demographic Stats Engine (Pandas/NumPy), and Media Manager (Pillow).
"""

import os
import pytest
from PIL import Image

from src.database.engine import DatabaseEngine
from src.database.repositories.person_repository import PersonRepository
from src.database.schema import EventModel, PlaceModel
from src.core.enums import Sex, EventType
from src.core.fuzzy_date import FuzzyDate
from src.gis.migration_engine import haversine_distance, MigrationEngine
from src.statistics.stats_engine import DemographicStatsEngine
from src.media.media_manager import MediaManager


@pytest.fixture
def db_engine():
    engine = DatabaseEngine(db_path=":memory:")
    engine.init_db()
    return engine


def test_haversine_distance():
    # Warsaw (52.2297, 21.0122) -> Krakow (50.0647, 19.9450) ~ 252 km
    dist = haversine_distance(52.2297, 21.0122, 50.0647, 19.9450)
    assert 240.0 < dist < 265.0


def test_migration_engine(db_engine):
    session = db_engine.get_session()
    person_repo = PersonRepository(session)
    p = person_repo.create_person(given_names="Adam", surname="Mickiewicz", sex=Sex.MALE)

    p1 = PlaceModel(name="Zaosie", latitude=53.548, longitude=26.069)
    p2 = PlaceModel(name="Paryż", latitude=48.856, longitude=2.352)
    session.add_all([p1, p2])
    session.flush()

    fd1 = FuzzyDate.parse("24 DEC 1798")
    fd2 = FuzzyDate.parse("26 NOV 1855")

    ev1 = EventModel(person_id=p.id, event_type=EventType.BIRTH, place_id=p1.id, date_raw="24 DEC 1798", jdn_min=fd1.jdn_min)
    ev2 = EventModel(person_id=p.id, event_type=EventType.DEATH, place_id=p2.id, date_raw="26 NOV 1855", jdn_min=fd2.jdn_min)
    session.add_all([ev1, ev2])
    session.commit()

    migration = MigrationEngine(session)
    trail = migration.get_person_migration_trail(p.id)

    assert len(trail) == 2
    assert trail[0].place_name == "Zaosie"
    assert trail[1].place_name == "Paryż"

    session.close()


def test_demographic_stats_engine(db_engine):
    session = db_engine.get_session()
    person_repo = PersonRepository(session)

    p1 = person_repo.create_person(given_names="Jan", surname="Kowalski", sex=Sex.MALE)
    p2 = person_repo.create_person(given_names="Anna", surname="Kowalska", sex=Sex.FEMALE)
    p3 = person_repo.create_person(given_names="Piotr", surname="Nowak", sex=Sex.MALE)
    session.commit()

    # Add birth and death for p1 (lifespan = 80)
    b = EventModel(person_id=p1.id, event_type=EventType.BIRTH, jdn_min=FuzzyDate.parse("1900").jdn_min)
    d = EventModel(person_id=p1.id, event_type=EventType.DEATH, jdn_min=FuzzyDate.parse("1980").jdn_min)
    session.add_all([b, d])
    session.commit()

    stats_engine = DemographicStatsEngine(session)
    summary = stats_engine.get_summary_statistics()

    assert summary["total_persons"] == 3
    assert summary["male_count"] == 2
    assert summary["female_count"] == 1
    assert summary["avg_lifespan"] > 75.0

    top_surnames = stats_engine.get_top_surnames(limit=5)
    assert len(top_surnames) >= 2
    assert top_surnames[0]["surname"] == "Kowalski" or top_surnames[0]["surname"] == "Kowalska"

    session.close()


def test_media_manager(db_engine, tmp_path):
    session = db_engine.get_session()
    person_repo = PersonRepository(session)
    p = person_repo.create_person(given_names="Jan", surname="Kowalski")
    session.commit()

    # Create dummy image file
    sample_img_path = str(tmp_path / "sample.jpg")
    img = Image.new("RGB", (300, 300), color="blue")
    img.save(sample_img_path)

    media_mgr = MediaManager(storage_dir=str(tmp_path / "media_storage"), session=session)
    media_obj = media_mgr.add_media(sample_img_path, title="Portret Jana", person_id=p.id)
    session.commit()

    assert media_obj.id is not None
    assert os.path.exists(media_obj.file_path)

    person_media = media_mgr.get_person_media(p.id)
    assert len(person_media) == 1
    assert person_media[0].title == "Portret Jana"

    session.close()
