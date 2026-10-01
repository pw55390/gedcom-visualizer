"""
Person Repository for managing Person entities, names, relationships, and queries.
"""

from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.orm import Session, joinedload

from src.core.enums import Sex, NameType
from src.database.schema import (
    PersonModel, PersonNameModel, FamilyChildModel, FamilySpouseModel, FamilyModel
)
from src.database.repositories.base import BaseRepository


class PersonRepository(BaseRepository[PersonModel]):
    def __init__(self, session: Session):
        super().__init__(session, PersonModel)

    def create_person(
        self,
        given_names: Optional[str] = None,
        surname: Optional[str] = None,
        sex: Sex = Sex.UNKNOWN,
        name_type: NameType = NameType.BIRTH
    ) -> PersonModel:
        """Creates a Person entity and attaches a primary PersonName."""
        person = PersonModel(sex=sex)
        self.session.add(person)
        self.session.flush()

        if given_names or surname:
            name = PersonNameModel(
                person_id=person.id,
                given_names=given_names,
                surname=surname,
                name_type=name_type
            )
            self.session.add(name)
            self.session.flush()
            person.primary_name_id = name.id
            self.session.flush()

        return person

    def get_by_id_with_details(self, person_id: str) -> Optional[PersonModel]:
        """Fetches a Person with preloaded names, events, and family relationships."""
        stmt = (
            select(PersonModel)
            .where(PersonModel.id == person_id)
            .options(
                joinedload(PersonModel.names),
                joinedload(PersonModel.events),
                joinedload(PersonModel.attributes),
                joinedload(PersonModel.family_as_child),
                joinedload(PersonModel.family_as_spouse)
            )
        )
        return self.session.scalars(stmt).first()

    def search_by_name(self, surname: Optional[str] = None, given_name: Optional[str] = None) -> List[PersonModel]:
        """Searches persons by surname and/or given name matching."""
        stmt = select(PersonModel).join(PersonModel.names)
        conditions = []
        if surname:
            conditions.append(PersonNameModel.surname.ilike(f"%{surname}%"))
        if given_name:
            conditions.append(PersonNameModel.given_names.ilike(f"%{given_name}%"))

        if conditions:
            stmt = stmt.where(*conditions)

        return list(self.session.scalars(stmt.distinct()).all())

    def get_parents(self, person_id: str) -> List[PersonModel]:
        """Returns list of parents for a given person."""
        stmt = (
            select(PersonModel)
            .join(FamilySpouseModel, PersonModel.id == FamilySpouseModel.person_id)
            .join(FamilyModel, FamilySpouseModel.family_id == FamilyModel.id)
            .join(FamilyChildModel, FamilyModel.id == FamilyChildModel.family_id)
            .where(FamilyChildModel.person_id == person_id)
        )
        return list(self.session.scalars(stmt).all())

    def get_children(self, person_id: str) -> List[PersonModel]:
        """Returns list of children for a given person."""
        stmt = (
            select(PersonModel)
            .join(FamilyChildModel, PersonModel.id == FamilyChildModel.person_id)
            .join(FamilyModel, FamilyChildModel.family_id == FamilyModel.id)
            .join(FamilySpouseModel, FamilyModel.id == FamilySpouseModel.family_id)
            .where(FamilySpouseModel.person_id == person_id)
        )
        return list(self.session.scalars(stmt.distinct()).all())
