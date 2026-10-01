"""
Unit tests for Database engine, schema, repositories, and FTS5 search.
"""

import pytest
from src.core.enums import Sex, NameType, UnionType, EventType, DateModifier
from src.core.fuzzy_date import FuzzyDate
from src.database.engine import DatabaseEngine
from src.database.schema import EventModel
from src.database.repositories.person_repository import PersonRepository
from src.database.repositories.family_repository import FamilyRepository
from src.database.repositories.fts_repository import FTSRepository


@pytest.fixture
def db_engine():
    engine = DatabaseEngine(db_path=":memory:")
    engine.init_db()
    return engine


def test_person_and_family_repositories(db_engine):
    session = db_engine.get_session()
    person_repo = PersonRepository(session)
    family_repo = FamilyRepository(session)

    # Create Father, Mother, Child
    father = person_repo.create_person(given_names="Jan", surname="Kowalski", sex=Sex.MALE)
    mother = person_repo.create_person(given_names="Anna", surname="Nowak", sex=Sex.FEMALE)
    child = person_repo.create_person(given_names="Piotr", surname="Kowalski", sex=Sex.MALE)

    session.commit()

    # Create Family
    family = family_repo.create_family(husband_id=father.id, wife_id=mother.id, union_type=UnionType.MARRIAGE)
    family_repo.add_child(family_id=family.id, child_id=child.id)
    session.commit()

    # Query parents and children
    parents = person_repo.get_parents(child.id)
    assert len(parents) == 2
    parent_ids = {p.id for p in parents}
    assert father.id in parent_ids
    assert mother.id in parent_ids

    children = person_repo.get_children(father.id)
    assert len(children) == 1
    assert children[0].id == child.id

    session.close()


def test_date_range_queries(db_engine):
    session = db_engine.get_session()
    person_repo = PersonRepository(session)
    
    person = person_repo.create_person(given_names="Adam", surname="Mickiewicz", sex=Sex.MALE)
    session.commit()

    fd_birth = FuzzyDate.parse("24 DEC 1798")
    event = EventModel(
        person_id=person.id,
        event_type=EventType.BIRTH,
        date_raw="24 DEC 1798",
        date_modifier=fd_birth.modifier,
        jdn_min=fd_birth.jdn_min,
        jdn_max=fd_birth.jdn_max,
        description="Narodziny Adama Mickiewicza"
    )
    session.add(event)
    session.commit()

    # Query events between 1790 and 1800
    fd_q_start = FuzzyDate.parse("1 JAN 1790")
    fd_q_end = FuzzyDate.parse("31 DEC 1800")

    from sqlalchemy import select
    stmt = select(EventModel).where(
        EventModel.jdn_min >= fd_q_start.jdn_min,
        EventModel.jdn_max <= fd_q_end.jdn_max
    )
    events = session.scalars(stmt).all()
    assert len(events) == 1
    assert events[0].description == "Narodziny Adama Mickiewicza"

    session.close()


def test_fts5_search(db_engine):
    session = db_engine.get_session()
    fts_repo = FTSRepository(session)

    fts_repo.index_entity(
        entity_id="p101",
        entity_type="PERSON",
        title="Jan Kowalski",
        content="Ur. 1850 r. w Warszawie. Znany działacz społeczny i niepodległościowy."
    )
    session.commit()

    results = fts_repo.search("Kowalski")
    assert len(results) == 1
    assert results[0]["entity_id"] == "p101"

    results_place = fts_repo.search("Warszawie")
    assert len(results_place) == 1

    session.close()
