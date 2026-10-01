"""
Unit and Integration Tests for GEDCOM Parser, Importer, Exporter, and Validator.
"""

import pytest
from src.database.engine import DatabaseEngine
from src.gedcom.parser import GedcomParser
from src.gedcom.importer import GedcomImporter
from src.gedcom.exporter import GedcomExporter
from src.gedcom.validator import DataValidator
from src.database.repositories.person_repository import PersonRepository
from src.database.repositories.fts_repository import FTSRepository


SAMPLE_GEDCOM = """0 HEAD
1 GEDC
2 VERS 5.5.1
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Jan /Kowalski/
2 GIVN Jan
2 SURN Kowalski
1 SEX M
1 BIRT
2 DATE 15 JAN 1900
2 PLAC Warszawa, Polska
1 DEAT
2 DATE 20 FEB 1980
2 PLAC Kraków, Polska
1 FAMS @F1@
0 @I2@ INDI
1 NAME Anna /Nowak/
2 GIVN Anna
2 SURN Nowak
1 SEX F
1 BIRT
2 DATE 10 MAY 1905
2 PLAC Poznań, Polska
1 FAMS @F1@
0 @I3@ INDI
1 NAME Piotr /Kowalski/
2 GIVN Piotr
2 SURN Kowalski
1 SEX M
1 BIRT
2 DATE 12 DEC 1930
2 PLAC Warszawa, Polska
1 FAMC @F1@
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
1 MARR
2 DATE 25 JUN 1928
2 PLAC Warszawa, Polska
0 TRLR
"""


@pytest.fixture
def db_engine():
    engine = DatabaseEngine(db_path=":memory:")
    engine.init_db()
    return engine


def test_gedcom_parser():
    parser = GedcomParser()
    records = parser.parse_string(SAMPLE_GEDCOM)
    assert len(records) == 6  # HEAD, I1, I2, I3, F1, TRLR
    
    indis = [r for r in records if r.tag == "INDI"]
    assert len(indis) == 3
    assert indis[0].xref == "@I1@"
    assert indis[0].get_sub_value("SEX") == "M"


def test_gedcom_import_and_query(db_engine):
    session = db_engine.get_session()
    parser = GedcomParser()
    records = parser.parse_string(SAMPLE_GEDCOM)

    importer = GedcomImporter(session)
    stats = importer.import_records(records)
    assert stats["persons"] == 3
    assert stats["families"] == 1

    person_repo = PersonRepository(session)
    persons = person_repo.search_by_name(surname="Kowalski")
    assert len(persons) == 2  # Jan and Piotr

    fts_repo = FTSRepository(session)
    fts_results = fts_repo.search("Kowalski")
    assert len(fts_results) >= 2

    session.close()


def test_gedcom_roundtrip(db_engine):
    session = db_engine.get_session()
    parser = GedcomParser()
    records = parser.parse_string(SAMPLE_GEDCOM)

    importer = GedcomImporter(session)
    importer.import_records(records)

    exporter = GedcomExporter(session)
    exported_gedcom = exporter.export_to_string()

    assert "INDI" in exported_gedcom
    assert "FAM" in exported_gedcom
    assert "/Kowalski/" in exported_gedcom
    assert "15 JAN 1900" in exported_gedcom
    assert "TRLR" in exported_gedcom

    session.close()


def test_data_validator_anachronism(db_engine):
    # Construct an impossible timeline (death before birth)
    ANOMALOUS_GEDCOM = """0 HEAD
0 @I99@ INDI
1 NAME Błędny /Rekord/
1 SEX M
1 BIRT
2 DATE 15 JAN 1950
1 DEAT
2 DATE 10 JAN 1900
0 TRLR
"""
    session = db_engine.get_session()
    parser = GedcomParser()
    records = parser.parse_string(ANOMALOUS_GEDCOM)

    importer = GedcomImporter(session)
    importer.import_records(records)

    validator = DataValidator(session)
    issues = validator.validate_all()

    assert len(issues) >= 1
    assert issues[0].category == "CHRONOLOGY"
    assert issues[0].severity == "ERROR"
    assert "wcześniejszą niż datę urodzenia" in issues[0].message

    session.close()


def test_myheritage_gedcom_parsing(db_engine):
    MYHERITAGE_SNIPPET = """0 HEAD
0 @S500022@ SOUR
1 TITL MyHeritage Family Trees
0 @I500548@ INDI
1 _UPD 19 JUL 2026 05:35:47 GMT -0500
1 NAME Katarzyna /Pękacka/
2 GIVN Katarzyna
2 SURN Pękacka
2 _MARNM Gutkiewicz
1 SEX F
1 BIRT
2 DATE 1836
2 PLAC Białobrzegi, Polska
1 DEAT Y
1 SOUR @S500022@
2 PAGE https://www.myheritage.pl/profile-1500960/katarzyna-gutkiewicz
2 QUAY 3
2 DATA
3 TEXT Osoba dodana przez Smart Match
1 RIN MH:I500548
1 _UID 6A4BD02A583198DB4F60655E614A1D5C
0 TRLR
"""
    session = db_engine.get_session()
    parser = GedcomParser()
    records = parser.parse_string(MYHERITAGE_SNIPPET)

    importer = GedcomImporter(session)
    stats = importer.import_records(records)
    assert stats["persons"] == 1

    person_repo = PersonRepository(session)
    persons = person_repo.search_by_name(surname="Pękacka")
    assert len(persons) == 1
    p = person_repo.get_by_id_with_details(persons[0].id)

    # Check Married Name (_MARNM)
    name_types = [n.name_type.value for n in p.names]
    assert "MARRIED" in name_types

    # Check Extra GEDCOM Attributes (_UPD, _UID, RIN)
    attr_tags = [a.tag for a in p.attributes]
    assert "_UPD" in attr_tags
    assert "_UID" in attr_tags
    assert "RIN" in attr_tags

    session.close()
