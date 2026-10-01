"""
Full-Text Search (FTS5) Repository for instant indexed searching across all entities.
"""

from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session


class FTSRepository:
    def __init__(self, session: Session):
        self.session = session

    def index_entity(self, entity_id: str, entity_type: str, title: str, content: str) -> None:
        """Indexes or updates an entity record inside SQLite FTS5 table."""
        # First remove existing entry for this entity
        self.session.execute(
            text("DELETE FROM fts_search_idx WHERE entity_id = :id AND entity_type = :type"),
            {"id": entity_id, "type": entity_type}
        )
        # Insert new index entry
        self.session.execute(
            text("""
                INSERT INTO fts_search_idx (entity_id, entity_type, title, content)
                VALUES (:id, :type, :title, :content)
            """),
            {"id": entity_id, "type": entity_type, "title": title or "", "content": content or ""}
        )
        self.session.flush()

    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Executes full-text match query against FTS5 table."""
        if not query or not query.strip():
            return []

        # Sanitize query for FTS5 syntax
        fts_query = f'"{query.strip()}*"'

        stmt = text("""
            SELECT entity_id, entity_type, title, content, snippet(fts_search_idx, 3, '<b>', '</b>', '...', 10) as snippet
            FROM fts_search_idx
            WHERE fts_search_idx MATCH :query
            ORDER BY rank
            LIMIT :limit
        """)
        
        results = self.session.execute(stmt, {"query": fts_query, "limit": limit}).fetchall()
        return [
            {
                "entity_id": r[0],
                "entity_type": r[1],
                "title": r[2],
                "content": r[3],
                "snippet": r[4]
            }
            for r in results
        ]
