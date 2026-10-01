"""
Unit tests for ReportLab PDF Builder and Report Templates.
"""

import os
import pytest

from src.database.engine import DatabaseEngine
from src.database.repositories.person_repository import PersonRepository
from src.core.enums import Sex, EventType
from src.reports.pdf_builder import ReportPdfBuilder
from src.reports.templates.person_report import PersonReportTemplate
from src.reports.templates.stats_report import StatsReportTemplate


@pytest.fixture
def db_engine():
    engine = DatabaseEngine(db_path=":memory:")
    engine.init_db()
    return engine


def test_pdf_builder_basic(tmp_path):
    pdf_file = str(tmp_path / "basic_test.pdf")
    builder = ReportPdfBuilder(pdf_file)
    builder.add_title("Testowy Tytuł Raportu")
    builder.add_heading("Nagłówek 1")
    builder.add_paragraph("To jest testowy akapit treści raportu.")
    builder.add_table([["Kolumna A", "Kolumna B"], ["Wartość 1", "Wartość 2"]])
    builder.build()

    assert os.path.exists(pdf_file)
    assert os.path.getsize(pdf_file) > 1000  # Non-empty valid PDF file


def test_person_report_template(db_engine, tmp_path):
    session = db_engine.get_session()
    person_repo = PersonRepository(session)
    p = person_repo.create_person(given_names="Maria", surname="Skłodowska-Curie", sex=Sex.FEMALE)
    session.commit()

    output_pdf = str(tmp_path / "karta_osobowa.pdf")
    template = PersonReportTemplate(session)
    template.generate_pdf(p.id, output_pdf)

    assert os.path.exists(output_pdf)
    assert os.path.getsize(output_pdf) > 1000

    session.close()


def test_stats_report_template(db_engine, tmp_path):
    session = db_engine.get_session()
    person_repo = PersonRepository(session)
    person_repo.create_person(given_names="Jan", surname="Kowalski", sex=Sex.MALE)
    person_repo.create_person(given_names="Anna", surname="Kowalska", sex=Sex.FEMALE)
    session.commit()

    output_pdf = str(tmp_path / "raport_statystyczny.pdf")
    template = StatsReportTemplate(session)
    template.generate_pdf(output_pdf)

    assert os.path.exists(output_pdf)
    assert os.path.getsize(output_pdf) > 1000

    session.close()
