"""
Abstract Base Repository implementation using SQLAlchemy 2.0.
"""

from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, session: Session, model_class: Type[T]):
        self.session = session
        self.model_class = model_class

    def get_by_id(self, entity_id: str) -> Optional[T]:
        return self.session.get(self.model_class, entity_id)

    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        stmt = select(self.model_class).limit(limit).offset(offset)
        return list(self.session.scalars(stmt).all())

    def add(self, entity: T) -> T:
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)
        self.session.flush()
