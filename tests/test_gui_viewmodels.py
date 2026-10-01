"""
Unit tests for MainViewModel, Qt Signal emissions, and Undo/Redo commands.
"""

import pytest
from PySide6.QtWidgets import QApplication
from src.database.engine import DatabaseEngine
from src.gui.viewmodels.main_viewmodel import MainViewModel
from src.core.enums import Sex


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def db_engine():
    engine = DatabaseEngine(db_path=":memory:")
    engine.init_db()
    return engine


def test_main_viewmodel_lifecycle(qapp, db_engine):
    vm = MainViewModel(db_engine)
    session = db_engine.get_session()

    # Create sample person
    p = vm.person_repo.create_person(given_names="Maria", surname="Skłodowska", sex=Sex.FEMALE)
    session.commit()

    # Index into FTS
    vm.fts_repo.index_entity(p.id, "PERSON", "Maria Skłodowska", "Płeć: F")
    session.commit()

    # Test Search
    results = []
    vm.search_results_updated.connect(results.extend)
    vm.search_persons("Skłodowska")
    assert len(results) >= 1
    assert results[0]["entity_id"] == p.id

    # Test Selection
    vm.select_person(p.id)
    details = vm.get_selected_person_details()
    assert details is not None
    assert details["given_names"] == "Maria"
    assert details["surname"] == "Skłodowska"

    session.close()


def test_main_viewmodel_undo_redo(qapp, db_engine):
    vm = MainViewModel(db_engine)
    session = db_engine.get_session()

    p = vm.person_repo.create_person(given_names="Jan", surname="Kowalski", sex=Sex.MALE)
    session.commit()

    vm.select_person(p.id)
    assert vm.get_selected_person_details()["surname"] == "Kowalski"

    # Perform Undoable update
    vm.update_person_name(p.id, "Jan", "Nowak-Kowalski")
    assert vm.get_selected_person_details()["surname"] == "Nowak-Kowalski"

    # Perform Undo
    vm.undo()
    assert vm.get_selected_person_details()["surname"] == "Kowalski"

    # Perform Redo
    vm.redo()
    assert vm.get_selected_person_details()["surname"] == "Nowak-Kowalski"

    session.close()
