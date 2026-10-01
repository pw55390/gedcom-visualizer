"""
Unit tests for GEDCOM Polish Translation Engine (i18n) & Dynamic Attribute Editing.
"""

import pytest
from src.core.i18n import translate_date_to_pl, translate_tag_to_pl
from src.database.engine import DatabaseEngine
from src.gui.viewmodels.main_viewmodel import MainViewModel


@pytest.fixture
def db_engine():
    engine = DatabaseEngine(db_path=":memory:")
    engine.init_db()
    return engine


def test_translate_date_to_pl():
    assert translate_date_to_pl("15 JAN 1900") == "15 sty 1900"
    assert translate_date_to_pl("ABT 1836") == "ok. 1836"
    assert translate_date_to_pl("BEF 1843") == "przed 1843"
    assert translate_date_to_pl("BET 1815 AND 1820") == "pomiędzy 1815 a 1820"
    assert translate_date_to_pl("20 MAY 1946") == "20 maj 1946"
    assert translate_date_to_pl("15 AUG 1821") == "15 sie 1821"


def test_translate_tag_to_pl():
    assert translate_tag_to_pl("BIRT") == "Urodzenie"
    assert translate_tag_to_pl("DEAT") == "Zgon"
    assert translate_tag_to_pl("OCCU") == "Zawód"
    assert translate_tag_to_pl("NOTE") == "Notatka"
    assert translate_tag_to_pl("_MARNM") == "Nazwisko po mężu"


def test_dynamic_attribute_editing(db_engine):
    session = db_engine.get_session()
    vm = MainViewModel(db_engine)

    from src.database.schema import PersonModel, PersonNameModel, Sex, NameType
    p = PersonModel(sex=Sex.FEMALE)
    session.add(p)
    session.flush()

    pn = PersonNameModel(person_id=p.id, given_names="Maria", surname="Kowalska", name_type=NameType.BIRTH)
    session.add(pn)
    session.commit()

    attrs_map = vm.get_person_attributes_map(p.id)
    assert "Imię / Imiona" in attrs_map
    assert "Nazwisko rodowe" in attrs_map
    assert "Nazwisko po ślubie / mężu (_MARNM)" in attrs_map
    assert attrs_map["Nazwisko rodowe"]["val"] == "Kowalska"

    # Update maiden surname
    vm.update_person_attribute(p.id, attrs_map["Nazwisko rodowe"], "Nowak")
    p_updated = vm.person_repo.get_by_id_with_details(p.id)
    assert p_updated.names[0].surname == "Nowak"

    # Update married surname (_MARNM)
    marnm_meta = attrs_map["Nazwisko po ślubie / mężu (_MARNM)"]
    vm.update_person_attribute(p.id, marnm_meta, "Wiszniewska")

    attrs_map2 = vm.get_person_attributes_map(p.id)
    assert attrs_map2["Nazwisko po ślubie / mężu (_MARNM)"]["val"] == "Wiszniewska"
