"""
Main ViewModel for Application State, Database Sessions, and Event Signaling.
Decouples Qt Views from Application Services and Repositories.
"""

from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, Signal

from src.database.engine import DatabaseEngine
from src.database.repositories.person_repository import PersonRepository
from src.database.repositories.family_repository import FamilyRepository
from src.database.repositories.fts_repository import FTSRepository
from src.gedcom.parser import GedcomParser
from src.gedcom.importer import GedcomImporter
from src.gedcom.exporter import GedcomExporter
from src.gedcom.validator import DataValidator, ValidationIssue
from src.application.undo_stack import UndoManager, UpdatePersonCommand


class MainViewModel(QObject):
    database_loaded = Signal(int)             # Emit total person count
    person_selected = Signal(str)             # Emit selected person_id
    search_results_updated = Signal(list)     # Emit search results list
    validation_completed = Signal(list)       # Emit list of ValidationIssue
    status_message = Signal(str)              # Emit status bar message

    def __init__(self, db_engine: Optional[DatabaseEngine] = None):
        super().__init__()
        self.db_engine = db_engine or DatabaseEngine(":memory:")
        self.db_engine.init_db()
        self.undo_manager = UndoManager()

        self.selected_person_id: Optional[str] = None
        self._refresh_repositories()

    def _refresh_repositories(self):
        self.session = self.db_engine.get_session()
        self.person_repo = PersonRepository(self.session)
        self.family_repo = FamilyRepository(self.session)
        self.fts_repo = FTSRepository(self.session)

    def import_gedcom(self, file_path: str):
        """Imports a GEDCOM file into the database and signals UI update."""
        parser = GedcomParser()
        records = parser.parse_file(file_path)

        importer = GedcomImporter(self.session)
        stats = importer.import_records(records)

        count = stats.get("persons", 0)
        self.status_message.emit(f"Pomyślnie zaimportowano {count} osób z pliku GEDCOM.")
        self.database_loaded.emit(count)
        self.search_persons("")  # Load all persons into UI list

    def export_gedcom(self, file_path: str):
        """Exports database records to a GEDCOM file."""
        exporter = GedcomExporter(self.session)
        content = exporter.export_to_string()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        self.status_message.emit(f"Wyeksportowano bazę danych do pliku {file_path}.")

    def search_persons(self, query: str, cached_nodes: Optional[dict] = None):
        """Ultra-fast sub-millisecond search across persons using in-memory token matching + FTS5 fallback."""
        query_str = query.strip()

        if not query_str:
            from sqlalchemy import select
            from sqlalchemy.orm import joinedload
            from src.database.schema import PersonModel
            stmt = select(PersonModel).options(joinedload(PersonModel.names)).limit(500)
            persons = self.session.scalars(stmt).unique().all()
            results = []
            for p in persons:
                name = p.names[0] if p.names else None
                name_str = f"{name.given_names or ''} {name.surname or ''}".strip() if name else "Brak nazwiska"
                results.append({
                    "id": p.id,
                    "title": name_str,
                    "snippet": f"Płeć: {p.sex.value}"
                })
            self.search_results_updated.emit(results)
            return

        # 1. Try Instant In-Memory Token Search if cached_nodes is provided
        if cached_nodes:
            tokens = query_str.lower().split()
            matched_results = []
            for node_id, data in cached_nodes.items():
                name_lower = data.get("name", "").lower()
                if all(t in name_lower for t in tokens):
                    matched_results.append({
                        "id": node_id,
                        "title": data.get("name", ""),
                        "snippet": f"Płeć: {data.get('sex', 'U')}"
                    })
                    if len(matched_results) >= 200:
                        break

            if matched_results:
                self.search_results_updated.emit(matched_results)
                return

        # 2. Fallback to FTS5 Search
        try:
            fts_matches = self.fts_repo.search(query_str)
            self.search_results_updated.emit(fts_matches)
        except Exception:
            self.search_results_updated.emit([])

    def select_person(self, person_id: str):
        """Selects a person and notifies listening UI docks."""
        self.selected_person_id = person_id
        self.person_selected.emit(person_id)

    def get_selected_person_details(self) -> Optional[Dict[str, Any]]:
        """Returns details dict for the currently selected person."""
        if not self.selected_person_id:
            return None

        p = self.person_repo.get_by_id_with_details(self.selected_person_id)
        if not p:
            return None

        name = p.names[0] if p.names else None
        parents = self.person_repo.get_parents(p.id)
        children = self.person_repo.get_children(p.id)

        return {
            "id": p.id,
            "given_names": name.given_names if name else "",
            "surname": name.surname if name else "",
            "sex": p.sex.value,
            "events_count": len(p.events),
            "parents_count": len(parents),
            "children_count": len(children)
        }

    def get_person_attributes_map(self, person_id: str) -> Dict[str, dict]:
        """Returns a dictionary mapping Polish attribute names to attribute details and current values."""
        p = self.person_repo.get_by_id_with_details(person_id)
        if not p:
            return {}

        from src.core.i18n import translate_tag_to_pl
        attrs = {}

        # 1. Names
        name = p.names[0] if p.names else None
        attrs["Imię / Imiona"] = {
            "type": "NAME_GIVEN", "val": name.given_names if name else "", "label": "Imię / Imiona"
        }
        attrs["Nazwisko rodowe"] = {
            "type": "NAME_SURN", "val": name.surname if name else "", "label": "Nazwisko rodowe"
        }

        # Married surname (_MARNM)
        marnm_attr = next((a for a in p.attributes if a.tag == "_MARNM"), None)
        attrs["Nazwisko po ślubie / mężu (_MARNM)"] = {
            "type": "NAME_MARNM",
            "attr_id": marnm_attr.id if marnm_attr else None,
            "val": marnm_attr.attribute_value if marnm_attr else "",
            "label": "Nazwisko po ślubie / mężu (_MARNM)"
        }

        # 2. Sex
        attrs["Płeć"] = {
            "type": "SEX", "val": p.sex.value, "label": "Płeć (MALE/FEMALE/OTHER)"
        }

        # 3. Events (Birth, Death, etc.)
        for ev in p.events:
            ev_label = translate_tag_to_pl(ev.event_type.value)
            dt_key = f"{ev_label} - Data"
            pl_key = f"{ev_label} - Miejsce"

            attrs[dt_key] = {
                "type": "EVENT_DATE", "event_id": ev.id, "val": ev.date_raw or "", "label": dt_key
            }
            if ev.place:
                attrs[pl_key] = {
                    "type": "EVENT_PLACE", "event_id": ev.id, "val": ev.place.name, "label": pl_key
                }

        # 4. Extra GEDCOM Attributes & Custom Fields (skipping _MARNM as it is explicit above)
        if p.attributes:
            for a in p.attributes:
                if a.tag == "_MARNM":
                    continue
                tag_pl = translate_tag_to_pl(a.tag)
                key_name = f"{tag_pl} ({a.tag})" if a.tag != tag_pl else a.tag
                attrs[key_name] = {
                    "type": "ATTRIBUTE", "attr_id": a.id, "val": a.attribute_value, "label": key_name
                }

        return attrs

    def update_person_attribute(self, person_id: str, attr_meta: dict, new_value: str):
        """Updates a specific person attribute with Undo/Redo support."""
        from src.database.schema import EventModel, PersonAttributeModel
        from src.core.enums import Sex

        a_type = attr_meta.get("type")
        old_val = attr_meta.get("val", "")

        def apply_fn(pid: str, val: str):
            p = self.person_repo.get_by_id_with_details(pid)
            if not p:
                return

            if a_type == "NAME_GIVEN":
                if p.names:
                    p.names[0].given_names = val
            elif a_type == "NAME_SURN":
                if p.names:
                    p.names[0].surname = val
            elif a_type == "NAME_MARNM":
                marnm_attr = next((a for a in p.attributes if a.tag == "_MARNM"), None)
                if marnm_attr:
                    marnm_attr.attribute_value = val
                elif val.strip():
                    new_attr = PersonAttributeModel(
                        person_id=pid,
                        tag="_MARNM",
                        attribute_key="_MARNM",
                        attribute_value=val.strip()
                    )
                    self.session.add(new_attr)
            elif a_type == "SEX":
                try:
                    p.sex = Sex(val.upper())
                except ValueError:
                    pass
            elif a_type == "EVENT_DATE":
                ev_id = attr_meta.get("event_id")
                ev = self.session.get(EventModel, ev_id)
                if ev:
                    ev.date_raw = val
            elif a_type == "EVENT_PLACE":
                ev_id = attr_meta.get("event_id")
                ev = self.session.get(EventModel, ev_id)
                if ev and ev.place:
                    ev.place.name = val
            elif a_type == "ATTRIBUTE":
                attr_id = attr_meta.get("attr_id")
                attr_obj = self.session.get(PersonAttributeModel, attr_id)
                if attr_obj:
                    attr_obj.attribute_value = val

            self.session.commit()
            self.session.expire_all()

            # Re-index FTS5
            name = p.names[0] if p.names else None
            full_name = f"{name.given_names or ''} {name.surname or ''}".strip() if name else "Brak nazwiska"
            self.fts_repo.index_entity(pid, "PERSON", full_name, f"Płeć: {p.sex.value}")
            self.session.commit()
            self.person_selected.emit(pid)

        cmd = UpdatePersonCommand(
            person_id=person_id,
            old_data={"val": old_val},
            new_data={"val": new_value},
            apply_fn=lambda pid, d: apply_fn(pid, d["val"]),
            description=f"Zmiana atrybutu '{attr_meta.get('label')}' -> {new_value}"
        )
        self.undo_manager.push(cmd)
        apply_fn(person_id, new_value)
        self.status_message.emit(f"Zaktualizowano atrybut '{attr_meta.get('label')}'.")

    def add_person_custom_attribute(self, person_id: str, tag: str, value: str):
        """Adds a new custom GEDCOM attribute to the person."""
        from src.database.schema import PersonAttributeModel
        attr = PersonAttributeModel(
            person_id=person_id,
            tag=tag.upper().strip(),
            attribute_key=tag.upper().strip(),
            attribute_value=value
        )
        self.session.add(attr)
        self.session.commit()
        self.person_selected.emit(person_id)
        self.status_message.emit(f"Dodano nowy atrybut '{tag}'.")

    def update_person_name(self, person_id: str, new_given: str, new_surname: str):
        """Updates a person's name using Undo/Redo command pattern."""
        p = self.person_repo.get_by_id_with_details(person_id)
        if not p or not p.names:
            return

        old_given = p.names[0].given_names or ""
        old_surname = p.names[0].surname or ""

        def apply_update(pid: str, data: dict):
            target = self.person_repo.get_by_id_with_details(pid)
            if target and target.names:
                target.names[0].given_names = data["given_names"]
                target.names[0].surname = data["surname"]
                self.session.commit()
                # Re-index FTS
                full_name = f"{data['given_names']} {data['surname']}".strip()
                self.fts_repo.index_entity(pid, "PERSON", full_name, f"Płeć: {target.sex.value}")
                self.session.commit()
                self.person_selected.emit(pid)

        cmd = UpdatePersonCommand(
            person_id=person_id,
            old_data={"given_names": old_given, "surname": old_surname},
            new_data={"given_names": new_given, "surname": new_surname},
            apply_fn=apply_update,
            description=f"Zmiana nazwiska {old_surname} -> {new_surname}"
        )
        self.undo_manager.push(cmd)
        apply_update(person_id, {"given_names": new_given, "surname": new_surname})
        self.status_message.emit("Zaktualizowano dane osoby.")

    def run_validation(self):
        """Runs logical anomaly validator."""
        validator = DataValidator(self.session)
        issues = validator.validate_all()
        self.validation_completed.emit(issues)
        self.status_message.emit(f"Walidacja zakończona: wykryto {len(issues)} uwag.")

    def undo(self):
        if self.undo_manager.can_undo():
            self.undo_manager.undo()
            self.status_message.emit("Cofnięto ostatnią operację.")

    def redo(self):
        if self.undo_manager.can_redo():
            self.undo_manager.redo()
            self.status_message.emit("Ponowiono operację.")
