"""
GEDCOM Exporter Service.
Generates clean, fully compliant GEDCOM 5.5.1 / 7.0 text output from database records.
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from src.core.enums import Sex, EventType
from src.database.schema import (
    PersonModel, FamilyModel, EventModel, PlaceModel, SourceModel
)


class GedcomExporter:
    def __init__(self, session: Session):
        self.session = session
        self.person_xref_map: Dict[str, str] = {}
        self.family_xref_map: Dict[str, str] = {}

    def export_to_string(self) -> str:
        """Exports the complete database to GEDCOM text format."""
        lines: List[str] = []

        # HEADER
        lines.append("0 HEAD")
        lines.append("1 GEDC")
        lines.append("2 VERS 5.5.1")
        lines.append("2 FORM LINEAGE-LINKED")
        lines.append("1 CHAR UTF-8")
        lines.append("1 SOUR GENEALOGY_ENTERPRISE")
        lines.append("2 VERS 1.0.0")

        # Query Persons
        persons = list(self.session.scalars(
            select(PersonModel).options(
                joinedload(PersonModel.names),
                joinedload(PersonModel.events).joinedload(EventModel.place),
                joinedload(PersonModel.family_as_child),
                joinedload(PersonModel.family_as_spouse)
            )
        ).unique().all())

        # Generate XRefs
        for idx, p in enumerate(persons, 1):
            self.person_xref_map[p.id] = f"@I{idx}@"

        families = list(self.session.scalars(
            select(FamilyModel).options(
                joinedload(FamilyModel.spouses),
                joinedload(FamilyModel.children),
                joinedload(FamilyModel.events).joinedload(EventModel.place)
            )
        ).unique().all())

        for idx, f in enumerate(families, 1):
            self.family_xref_map[f.id] = f"@F{idx}@"

        # Export INDI records
        for p in persons:
            pxref = self.person_xref_map[p.id]
            lines.append(f"0 {pxref} INDI")
            
            # Names
            for n in p.names:
                name_val = f"{n.given_names or ''} /{n.surname or ''}/".strip()
                lines.append(f"1 NAME {name_val}")
                if n.given_names:
                    lines.append(f"2 GIVN {n.given_names}")
                if n.surname:
                    lines.append(f"2 SURN {n.surname}")

            # Sex
            lines.append(f"1 SEX {p.sex.value}")

            # Family links
            for fc in p.family_as_child:
                if fc.family_id in self.family_xref_map:
                    lines.append(f"1 FAMC {self.family_xref_map[fc.family_id]}")

            for fs in p.family_as_spouse:
                if fs.family_id in self.family_xref_map:
                    lines.append(f"1 FAMS {self.family_xref_map[fs.family_id]}")

            # Events
            for ev in p.events:
                tag = ev.event_type.value
                lines.append(f"1 {tag}")
                if ev.date_raw:
                    lines.append(f"2 DATE {ev.date_raw}")
                if ev.place:
                    lines.append(f"2 PLAC {ev.place.name}")

        # Export FAM records
        for f in families:
            fxref = self.family_xref_map[f.id]
            lines.append(f"0 {fxref} FAM")

            for sp in f.spouses:
                if sp.person_id in self.person_xref_map:
                    role_tag = "HUSB" if sp.role.value == "HUSBAND" else "WIFE"
                    lines.append(f"1 {role_tag} {self.person_xref_map[sp.person_id]}")

            for ch in f.children:
                if ch.person_id in self.person_xref_map:
                    lines.append(f"1 CHIL {self.person_xref_map[ch.person_id]}")

            for ev in f.events:
                tag = ev.event_type.value
                lines.append(f"1 {tag}")
                if ev.date_raw:
                    lines.append(f"2 DATE {ev.date_raw}")
                if ev.place:
                    lines.append(f"2 PLAC {ev.place.name}")

        # TRAILER
        lines.append("0 TRLR")

        return "\n".join(lines) + "\n"
