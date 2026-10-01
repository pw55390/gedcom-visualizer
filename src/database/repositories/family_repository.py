"""
Family Repository for managing Family unions, spouses, and children relationships.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.core.enums import UnionType, SpouseRole, ParentChildRelType
from src.database.schema import FamilyModel, FamilySpouseModel, FamilyChildModel
from src.database.repositories.base import BaseRepository


class FamilyRepository(BaseRepository[FamilyModel]):
    def __init__(self, session: Session):
        super().__init__(session, FamilyModel)

    def create_family(
        self,
        husband_id: Optional[str] = None,
        wife_id: Optional[str] = None,
        union_type: UnionType = UnionType.MARRIAGE
    ) -> FamilyModel:
        """Creates a family union and links husband and/or wife."""
        family = FamilyModel(union_type=union_type)
        self.session.add(family)
        self.session.flush()

        if husband_id:
            sp_h = FamilySpouseModel(family_id=family.id, person_id=husband_id, role=SpouseRole.HUSBAND)
            self.session.add(sp_h)

        if wife_id:
            sp_w = FamilySpouseModel(family_id=family.id, person_id=wife_id, role=SpouseRole.WIFE)
            self.session.add(sp_w)

        self.session.flush()
        return family

    def add_child(
        self,
        family_id: str,
        child_id: str,
        rel_type: ParentChildRelType = ParentChildRelType.BIOLOGICAL
    ) -> FamilyChildModel:
        """Adds a child to a family union."""
        fc = FamilyChildModel(family_id=family_id, person_id=child_id, rel_type=rel_type)
        self.session.add(fc)
        self.session.flush()
        return fc

    def get_by_id_with_members(self, family_id: str) -> Optional[FamilyModel]:
        """Fetches a family with preloaded spouses, children, and events."""
        stmt = (
            select(FamilyModel)
            .where(FamilyModel.id == family_id)
            .options(
                joinedload(FamilyModel.spouses).joinedload(FamilySpouseModel.person),
                joinedload(FamilyModel.children).joinedload(FamilyChildModel.person),
                joinedload(FamilyModel.events)
            )
        )
        return self.session.scalars(stmt).first()
