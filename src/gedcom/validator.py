"""
GEDCOM & Database Integrity and Anachronism Validator.
Detects logical anomalies (anachronisms, impossible ages, broken links).
"""

from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from src.core.enums import EventType
from src.database.schema import PersonModel, FamilyModel, EventModel, FamilySpouseModel, FamilyChildModel


@dataclass
class ValidationIssue:
    severity: str  # "ERROR", "WARNING", "INFO"
    category: str
    entity_id: str
    message: str


class DataValidator:
    def __init__(self, session: Session):
        self.session = session

    def validate_all(self) -> List[ValidationIssue]:
        """Runs all integrity and chronological anomaly validations across the database."""
        issues: List[ValidationIssue] = []
        issues.extend(self._validate_lifespans_and_chronology())
        issues.extend(self._validate_parent_child_chronology())
        issues.extend(self._validate_marriage_chronology())
        return issues

    def _validate_lifespans_and_chronology(self) -> List[ValidationIssue]:
        issues = []
        persons = self.session.scalars(
            select(PersonModel).options(joinedload(PersonModel.events), joinedload(PersonModel.names))
        ).unique().all()

        for p in persons:
            name_str = p.names[0].surname if p.names else p.id
            birth_event = next((e for e in p.events if e.event_type == EventType.BIRTH), None)
            death_event = next((e for e in p.events if e.event_type == EventType.DEATH), None)

            if birth_event and death_event and birth_event.jdn_min and death_event.jdn_max:
                # Death before birth
                if death_event.jdn_max < birth_event.jdn_min:
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        category="CHRONOLOGY",
                        entity_id=p.id,
                        message=f"Osoba '{name_str}' ma datę zgonu wcześniejszą niż datę urodzenia."
                    ))

                # Lifespan > 120 years (~43830 days)
                lifespan_days = death_event.jdn_max - birth_event.jdn_min
                if lifespan_days > 43830:
                    years = lifespan_days // 365
                    issues.append(ValidationIssue(
                        severity="WARNING",
                        category="LIFESPAN",
                        entity_id=p.id,
                        message=f"Osoba '{name_str}' żyła ponad {years} lat ({lifespan_days} dni) - prawdopodobny błąd w datach."
                    ))

        return issues

    def _validate_parent_child_chronology(self) -> List[ValidationIssue]:
        issues = []
        families = self.session.scalars(
            select(FamilyModel).options(
                joinedload(FamilyModel.spouses).joinedload(FamilySpouseModel.person).joinedload(PersonModel.events),
                joinedload(FamilyModel.children).joinedload(FamilyChildModel.person).joinedload(PersonModel.events)
            )
        ).unique().all()

        for fam in families:
            parents = [sp.person for sp in fam.spouses if sp.person]
            children = [ch.person for ch in fam.children if ch.person]

            for child in children:
                c_birth = next((e for e in child.events if e.event_type == EventType.BIRTH), None)
                if not c_birth or not c_birth.jdn_min:
                    continue

                for parent in parents:
                    p_birth = next((e for e in parent.events if e.event_type == EventType.BIRTH), None)
                    if p_birth and p_birth.jdn_min:
                        # Parent born after child
                        if p_birth.jdn_min >= c_birth.jdn_min:
                            issues.append(ValidationIssue(
                                severity="ERROR",
                                category="ANACHRONISM",
                                entity_id=child.id,
                                message=f"Dziecko (ID: {child.id}) urodziło się przed lub w tym samym czasie co rodzic (ID: {parent.id})."
                            ))

        return issues

    def _validate_marriage_chronology(self) -> List[ValidationIssue]:
        issues = []
        families = self.session.scalars(
            select(FamilyModel).options(
                joinedload(FamilyModel.events),
                joinedload(FamilyModel.spouses).joinedload(FamilySpouseModel.person).joinedload(PersonModel.events)
            )
        ).unique().all()

        for fam in families:
            marr_event = next((e for e in fam.events if e.event_type == EventType.MARRIAGE), None)
            if not marr_event or not marr_event.jdn_min:
                continue

            for sp in fam.spouses:
                if not sp.person:
                    continue
                p_birth = next((e for e in sp.person.events if e.event_type == EventType.BIRTH), None)
                if p_birth and p_birth.jdn_min:
                    if marr_event.jdn_min < p_birth.jdn_min:
                        issues.append(ValidationIssue(
                            severity="ERROR",
                            category="CHRONOLOGY",
                            entity_id=fam.id,
                            message=f"Ślub rodziny (ID: {fam.id}) nastąpił przed narodzinami małżonka (ID: {sp.person.id})."
                        ))

        return issues
