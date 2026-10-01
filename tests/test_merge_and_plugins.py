"""
Unit tests for Deduplication & Merge Engine and Pluggy Plugin Architecture.
"""

import pytest
from src.database.engine import DatabaseEngine
from src.database.repositories.person_repository import PersonRepository
from src.database.repositories.family_repository import FamilyRepository
from src.core.enums import Sex
from src.application.merge_engine import levenshtein_similarity, MergeEngine
from src.plugins.plugin_manager import PluginManager, hookimpl


@pytest.fixture
def db_engine():
    engine = DatabaseEngine(db_path=":memory:")
    engine.init_db()
    return engine


def test_levenshtein_similarity():
    assert levenshtein_similarity("Kowalski", "Kowalski") == 1.0
    assert levenshtein_similarity("Kowalski", "Kowalska") > 0.85
    assert levenshtein_similarity("Kowalski", "Nowak") <= 0.5


def test_merge_engine_deduplication(db_engine):
    session = db_engine.get_session()
    person_repo = PersonRepository(session)
    family_repo = FamilyRepository(session)

    # Create two duplicate person records
    p1 = person_repo.create_person(given_names="Jan", surname="Kowalski", sex=Sex.MALE)
    p2 = person_repo.create_person(given_names="Jan", surname="Kowalsky", sex=Sex.MALE)
    child = person_repo.create_person(given_names="Piotr", surname="Kowalski", sex=Sex.MALE)
    session.commit()

    f = family_repo.create_family(husband_id=p2.id)
    family_repo.add_child(f.id, child.id)
    session.commit()

    merge_eng = MergeEngine(session)
    candidates = merge_eng.find_duplicate_candidates(min_confidence=0.7)
    assert len(candidates) >= 1

    # Merge p2 into p1
    merged = merge_eng.merge_persons(primary_id=p1.id, duplicate_id=p2.id)
    assert merged.id == p1.id

    # Verify children of p1 now include child
    children_p1 = person_repo.get_children(p1.id)
    assert len(children_p1) == 1
    assert children_p1[0].id == child.id

    session.close()


def test_plugin_manager():
    pm = PluginManager()

    events_log = []

    class SamplePlugin:
        @hookimpl
        def on_person_created(self, person_id: str, full_name: str):
            events_log.append(f"CREATED:{full_name}")

        @hookimpl
        def custom_validation_rule(self, person_id: str):
            return "Plugin Warning: Custom rule checked."

    pm.register_plugin(SamplePlugin())
    pm.notify_person_created("p100", "Adam Mickiewicz")

    assert len(events_log) == 1
    assert events_log[0] == "CREATED:Adam Mickiewicz"

    res = pm.run_custom_validations("p100")
    assert "Plugin Warning: Custom rule checked." in res
