"""
GEDCOM Data Importer Service.
Transforms GedcomRecord trees into SQLAlchemy relational entities and FTS5 search indexes.
"""

import re
from typing import Dict, List, Optional, Callable
from sqlalchemy.orm import Session

from src.core.enums import Sex, NameType, UnionType, SpouseRole, ParentChildRelType, EventType, DateModifier
from src.core.fuzzy_date import FuzzyDate
from src.database.schema import (
    PersonModel, PersonNameModel, FamilyModel, FamilySpouseModel,
    FamilyChildModel, EventModel, PlaceModel, SourceModel, CitationModel, PersonAttributeModel
)
from src.database.repositories.person_repository import PersonRepository
from src.database.repositories.family_repository import FamilyRepository
from src.database.repositories.fts_repository import FTSRepository
from src.gedcom.structure import GedcomRecord


class GedcomImporter:
    def __init__(self, session: Session, progress_callback: Optional[Callable[[float, str], None]] = None):
        self.session = session
        self.progress_callback = progress_callback
        self.person_repo = PersonRepository(session)
        self.family_repo = FamilyRepository(session)
        self.fts_repo = FTSRepository(session)

        # Mapping XRefs (e.g. @I1@) to DB UUIDs
        self.person_xref_map: Dict[str, str] = {}
        self.family_xref_map: Dict[str, str] = {}
        self.source_xref_map: Dict[str, str] = {}
        self.place_cache: Dict[str, PlaceModel] = {}

    def import_records(self, records: List[GedcomRecord]) -> Dict[str, int]:
        """Imports top-level GEDCOM records into the database in optimal batch order."""
        stats = {"persons": 0, "families": 0, "sources": 0, "events": 0}

        sources = [r for r in records if r.tag == "SOUR" and r.xref]
        indis = [r for r in records if r.tag == "INDI" and r.xref]
        fams = [r for r in records if r.tag == "FAM" and r.xref]

        # Step 1: Import Sources
        for src_rec in sources:
            source_obj = SourceModel(
                title=src_rec.get_sub_value("TITL") or "Nieznane źródło",
                author=src_rec.get_sub_value("AUTH"),
                publication_info=src_rec.get_sub_value("PUBL")
            )
            self.session.add(source_obj)
            self.session.flush()
            self.source_xref_map[src_rec.xref] = source_obj.id
            stats["sources"] += 1

        # Step 2: Import Persons (INDI)
        total_indis = len(indis)
        for idx, indi_rec in enumerate(indis):
            if self.progress_callback and total_indis > 0 and idx % 100 == 0:
                self.progress_callback(0.2 + 0.5 * (idx / total_indis), f"Importowanie osób ({idx}/{total_indis})")

            person_db = self._import_person(indi_rec)
            self.person_xref_map[indi_rec.xref] = person_db.id
            stats["persons"] += 1

        self.session.flush()

        # Step 3: Import Families & Links (FAM)
        total_fams = len(fams)
        for idx, fam_rec in enumerate(fams):
            if self.progress_callback and total_fams > 0 and idx % 100 == 0:
                self.progress_callback(0.7 + 0.3 * (idx / total_fams), f"Importowanie rodzin ({idx}/{total_fams})")

            fam_db = self._import_family(fam_rec)
            self.family_xref_map[fam_rec.xref] = fam_db.id
            stats["families"] += 1

        self.session.commit()

        if self.progress_callback:
            self.progress_callback(1.0, "Import bazy danych zakończony sukcesem")

        return stats

    def _import_person(self, indi_rec: GedcomRecord) -> PersonModel:
        # Determine sex
        sex_str = indi_rec.get_sub_value("SEX")
        sex = Sex.UNKNOWN
        if sex_str == "M":
            sex = Sex.MALE
        elif sex_str == "F":
            sex = Sex.FEMALE
        elif sex_str == "X":
            sex = Sex.OTHER

        person = PersonModel(sex=sex)
        self.session.add(person)
        self.session.flush()

        # Process Names & Married Names (_MARNM)
        full_name_title = ""
        for name_rec in indi_rec.get_sub_records("NAME"):
            name_val = name_rec.value or ""
            given = name_rec.get_sub_value("GIVN")
            surname = name_rec.get_sub_value("SURN")

            if not surname and "/" in name_val:
                match = re.search(r"/([^/]+)/", name_val)
                if match:
                    surname = match.group(1)
                given = re.sub(r"/([^/]+)/", "", name_val).strip()

            if not given and not surname:
                given = name_val.strip()

            pn = PersonNameModel(
                person_id=person.id,
                given_names=given,
                surname=surname,
                name_type=NameType.BIRTH
            )
            self.session.add(pn)
            self.session.flush()

            if not person.primary_name_id:
                person.primary_name_id = pn.id

            name_str = f"{given or ''} {surname or ''}".strip()
            if name_str:
                full_name_title = name_str

            # Married name (_MARNM)
            marnm = name_rec.get_sub_value("_MARNM")
            if marnm:
                pn_m = PersonNameModel(
                    person_id=person.id,
                    given_names=given,
                    surname=marnm,
                    name_type=NameType.MARRIED
                )
                self.session.add(pn_m)

        # Index into FTS5
        self.fts_repo.index_entity(
            entity_id=person.id,
            entity_type="PERSON",
            title=full_name_title or "Osoba bez nazwiska",
            content=f"Płeć: {sex.value}"
        )

        # Process Personal Events (standard + EVEN with TYPE)
        for ev_tag, ev_type in [
            ("BIRT", EventType.BIRTH), ("CHR", EventType.BAPTISM),
            ("DEAT", EventType.DEATH), ("BURI", EventType.BURIAL),
            ("EMIG", EventType.EMIGRATION), ("IMMI", EventType.IMMIGRATION),
            ("CENS", EventType.CENSUS), ("OCCU", EventType.OCCUPATION),
            ("RESI", EventType.RESIDENCE)
        ]:
            for ev_rec in indi_rec.get_sub_records(ev_tag):
                self._import_event(ev_rec, ev_type, person_id=person.id)

        # Generic EVEN tags (e.g. 1 EVEN / 2 TYPE MARR or Ślub)
        for ev_rec in indi_rec.get_sub_records("EVEN"):
            ev_type_val = ev_rec.get_sub_value("TYPE")
            ev_type = EventType.CUSTOM
            if ev_type_val == "MARR" or ev_type_val == "Ślub":
                ev_type = EventType.MARRIAGE
            self._import_event(ev_rec, ev_type, person_id=person.id)

        # Import Extra GEDCOM attributes / custom records (_UPD, _UID, RIN, SOUR, etc.)
        for sub_rec in indi_rec.sub_records:
            if sub_rec.tag not in ("SEX", "NAME", "BIRT", "CHR", "DEAT", "BURI", "EMIG", "IMMI", "CENS", "FAMC", "FAMS", "CHAN"):
                val = sub_rec.get_full_value()
                if val:
                    attr = PersonAttributeModel(
                        person_id=person.id,
                        tag=sub_rec.tag,
                        attribute_key=sub_rec.tag,
                        attribute_value=val
                    )
                    self.session.add(attr)

        return person

    def _import_family(self, fam_rec: GedcomRecord) -> FamilyModel:
        fam = FamilyModel(union_type=UnionType.MARRIAGE)
        self.session.add(fam)
        self.session.flush()

        # Spouses
        husb_xref = fam_rec.get_sub_value("HUSB")
        if husb_xref and husb_xref in self.person_xref_map:
            sp_h = FamilySpouseModel(family_id=fam.id, person_id=self.person_xref_map[husb_xref], role=SpouseRole.HUSBAND)
            self.session.add(sp_h)

        wife_xref = fam_rec.get_sub_value("WIFE")
        if wife_xref and wife_xref in self.person_xref_map:
            sp_w = FamilySpouseModel(family_id=fam.id, person_id=self.person_xref_map[wife_xref], role=SpouseRole.WIFE)
            self.session.add(sp_w)

        # Children
        for chil_rec in fam_rec.get_sub_records("CHIL"):
            chil_xref = chil_rec.value
            if chil_xref and chil_xref in self.person_xref_map:
                fc = FamilyChildModel(
                    family_id=fam.id,
                    person_id=self.person_xref_map[chil_xref],
                    rel_type=ParentChildRelType.BIOLOGICAL
                )
                self.session.add(fc)

        # Family Events (MARR, DIV, etc.)
        for ev_rec in fam_rec.get_sub_records("MARR"):
            self._import_event(ev_rec, EventType.MARRIAGE, family_id=fam.id)

        for ev_rec in fam_rec.get_sub_records("DIV"):
            self._import_event(ev_rec, EventType.DIVORCE, family_id=fam.id)

        return fam

    def _import_event(self, ev_rec: GedcomRecord, event_type: EventType, person_id: Optional[str] = None, family_id: Optional[str] = None) -> EventModel:
        date_str = ev_rec.get_sub_value("DATE")
        place_str = ev_rec.get_sub_value("PLAC")

        if not place_str:
            addr_recs = ev_rec.get_sub_records("ADDR")
            if addr_recs:
                addr_rec = addr_recs[0]
                adr1 = addr_rec.get_sub_value("ADR1") or addr_rec.value or ""
                city = addr_rec.get_sub_value("CITY") or ""
                ctry = addr_rec.get_sub_value("CTRY") or ""
                parts = [p for p in [adr1, city, ctry] if p]
                if parts:
                    place_str = ", ".join(parts)

        fd = FuzzyDate.parse(date_str) if date_str else None
        place_obj = self._get_or_create_place(place_str) if place_str else None

        ev = EventModel(
            event_type=event_type,
            date_raw=date_str,
            date_modifier=fd.modifier if fd else DateModifier.EXACT,
            jdn_min=fd.jdn_min if fd else None,
            jdn_max=fd.jdn_max if fd else None,
            person_id=person_id,
            family_id=family_id,
            place_id=place_obj.id if place_obj else None,
            description=ev_rec.get_full_value()
        )
        self.session.add(ev)
        self.session.flush()

        # Import Citations (SOUR) attached to event
        for sour_rec in ev_rec.get_sub_records("SOUR"):
            sour_xref = sour_rec.value
            if sour_xref and sour_xref in self.source_xref_map:
                page_ref = sour_rec.get_sub_value("PAGE")
                quay_str = sour_rec.get_sub_value("QUAY")
                text_quote = None

                data_recs = sour_rec.get_sub_records("DATA")
                if data_recs:
                    text_quote = data_recs[0].get_sub_value("TEXT")

                cit = CitationModel(
                    source_id=self.source_xref_map[sour_xref],
                    person_id=person_id,
                    event_id=ev.id,
                    page_reference=page_ref,
                    confidence=int(quay_str) if quay_str and quay_str.isdigit() else 3,
                    text_quote=text_quote
                )
                self.session.add(cit)

        return ev

    def _get_or_create_place(self, place_name: str) -> PlaceModel:
        clean_name = place_name.strip()
        if clean_name in self.place_cache:
            return self.place_cache[clean_name]

        place = PlaceModel(name=clean_name)
        self.session.add(place)
        self.session.flush()
        self.place_cache[clean_name] = place
        return place
