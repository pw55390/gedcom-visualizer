"""
Person Dossier (Karta Osobowa) PDF Generator Template.
"""

from typing import Optional
from sqlalchemy.orm import Session

from src.database.repositories.person_repository import PersonRepository
from src.reports.pdf_builder import ReportPdfBuilder


class PersonReportTemplate:
    def __init__(self, session: Session):
        self.session = session
        self.person_repo = PersonRepository(session)

    def generate_pdf(self, person_id: str, output_path: str):
        """Generates a detailed Person Dossier PDF document."""
        person = self.person_repo.get_by_id_with_details(person_id)
        if not person:
            raise ValueError(f"Nie znaleziono osoby o ID {person_id}")

        name = person.names[0] if person.names else None
        full_name = f"{name.given_names or ''} {name.surname or ''}".strip() if name else "Brak nazwiska"

        builder = ReportPdfBuilder(output_path)
        builder.add_title(f"Karta Osobowa: {full_name}")
        builder.add_paragraph(f"<b>ID Encji:</b> {person.id}")
        builder.add_paragraph(f"<b>Płeć:</b> {person.sex.value}")

        # Parents
        parents = self.person_repo.get_parents(person.id)
        parent_names = [
            f"{p.names[0].given_names or ''} {p.names[0].surname or ''}".strip()
            for p in parents if p.names
        ]
        builder.add_paragraph(f"<b>Rodzice:</b> {', '.join(parent_names) if parent_names else 'Brak danych'}")

        # Children
        children = self.person_repo.get_children(person.id)
        child_names = [
            f"{c.names[0].given_names or ''} {c.names[0].surname or ''}".strip()
            for c in children if c.names
        ]
        builder.add_paragraph(f"<b>Dzieci:</b> {', '.join(child_names) if child_names else 'Brak danych'}")

        # Events Table
        from src.core.i18n import translate_date_to_pl, translate_tag_to_pl
        builder.add_heading("Zdarzenia i Fakty Życiowe")
        if person.events:
            table_data = [["Typ Zdarzenia", "Data", "Miejsce", "Opis"]]
            for ev in person.events:
                table_data.append([
                    translate_tag_to_pl(ev.event_type.value),
                    translate_date_to_pl(ev.date_raw or "-"),
                    ev.place.name if ev.place else "-",
                    ev.description or "-"
                ])
            builder.add_table(table_data, col_widths=[100, 100, 120, 167])
        else:
            builder.add_paragraph("Brak zarejestrowanych zdarzeń.")

        # Extra GEDCOM Attributes & Notes
        if person.attributes:
            builder.add_heading("Dodatkowe Informacje z GEDCOM")
            attr_table = [["Atrybut / Tag", "Treść / Notatka"]]
            for attr in person.attributes:
                attr_table.append([translate_tag_to_pl(attr.tag), attr.attribute_value])
            builder.add_table(attr_table, col_widths=[120, 367])

        builder.build()
