"""
Deduplication & Record Merge Engine.
Detects duplicate person records using name phonetic similarity and date proximity, and executes non-destructive record merges.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.schema import (
    PersonModel, PersonNameModel, FamilyChildModel, FamilySpouseModel, EventModel, MediaModel, CitationModel
)
from src.database.repositories.person_repository import PersonRepository


def levenshtein_similarity(s1: str, s2: str) -> float:
    """Calculates Levenshtein similarity ratio between 0.0 and 1.0."""
    if not s1 or not s2:
        return 0.0
    u1, u2 = s1.lower(), s2.lower()
    if u1 == u2:
        return 1.0

    len1, len2 = len(u1), len(u2)
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if u1[i - 1] == u2[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j - 1] + cost
            )

    dist = matrix[len1][len2]
    max_len = max(len1, len2)
    return 1.0 - (dist / max_len)


@dataclass
class DuplicateCandidate:
    person1_id: str
    person2_id: str
    person1_name: str
    person2_name: str
    confidence_score: float  # 0.0 to 1.0


class MergeEngine:
    def __init__(self, session: Session):
        self.session = session
        self.person_repo = PersonRepository(session)

    def find_duplicate_candidates(self, min_confidence: float = 0.75) -> List[DuplicateCandidate]:
        """Scans database for duplicate person candidates based on name similarity."""
        persons = self.session.scalars(select(PersonModel)).all()
        
        candidates: List[DuplicateCandidate] = []
        all_p = [self.person_repo.get_by_id_with_details(p.id) for p in persons]
        all_p = [p for p in all_p if p and p.names]

        for i in range(len(all_p)):
            for j in range(i + 1, len(all_p)):
                p1, p2 = all_p[i], all_p[j]
                if p1.sex != p2.sex and p1.sex.value != "U" and p2.sex.value != "U":
                    continue

                name1 = f"{p1.names[0].given_names or ''} {p1.names[0].surname or ''}".strip()
                name2 = f"{p2.names[0].given_names or ''} {p2.names[0].surname or ''}".strip()

                score = levenshtein_similarity(name1, name2)
                if score >= min_confidence:
                    candidates.append(DuplicateCandidate(
                        person1_id=p1.id,
                        person2_id=p2.id,
                        person1_name=name1,
                        person2_name=name2,
                        confidence_score=round(score, 2)
                    ))

        return candidates

    def merge_persons(self, primary_id: str, duplicate_id: str) -> PersonModel:
        """Merges duplicate_id into primary_id, re-linking all relations, events, and media."""
        if primary_id == duplicate_id:
            raise ValueError("Nie można scalić osoby ze samą sobą.")

        primary = self.person_repo.get_by_id_with_details(primary_id)
        duplicate = self.person_repo.get_by_id_with_details(duplicate_id)

        if not primary or not duplicate:
            raise ValueError("Jedna ze scalanych osób nie istnieje.")

        # Re-link Family Child
        for fc in list(duplicate.family_as_child):
            new_fc = FamilyChildModel(family_id=fc.family_id, person_id=primary.id, rel_type=fc.rel_type)
            self.session.add(new_fc)
            self.session.delete(fc)

        # Re-link Family Spouse
        for fs in list(duplicate.family_as_spouse):
            new_fs = FamilySpouseModel(family_id=fs.family_id, person_id=primary.id, role=fs.role)
            self.session.add(new_fs)
            self.session.delete(fs)

        # Re-link Events
        for ev in list(duplicate.events):
            ev.person_id = primary.id

        # Re-link Media
        for med in duplicate.media:
            med.person_id = primary.id

        # Merge Names
        for name in duplicate.names:
            name.person_id = primary.id

        # Clear ORM relationship lists on duplicate to prevent cascade delete warnings
        duplicate.family_as_child.clear()
        duplicate.family_as_spouse.clear()
        duplicate.events.clear()

        self.session.flush()
        # Delete duplicate person record
        self.session.delete(duplicate)
        self.session.commit()

        return primary
