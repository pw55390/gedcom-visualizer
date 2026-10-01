"""
Database Engine Manager for SQLite + SQLAlchemy 2.0.
Handles Pragmas (WAL, Foreign Keys), Schema Initialization, and FTS5 Virtual Tables.
"""

from typing import Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from src.database.schema import Base


class DatabaseEngine:
    def __init__(self, db_path: str = ":memory:", echo: bool = False):
        if db_path == ":memory:":
            self.url = "sqlite:///:memory:"
        elif db_path.startswith("sqlite:///"):
            self.url = db_path
        else:
            self.url = f"sqlite:///{db_path}"

        self.engine = create_engine(self.url, echo=echo)
        self._configure_sqlite_pragmas()
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    def _configure_sqlite_pragmas(self):
        """Enforces Foreign Key constraints and WAL mode on every SQLite connection."""
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.close()

    def init_db(self):
        """Creates all database tables and initializes the FTS5 full-text index."""
        Base.metadata.create_all(self.engine)
        self._init_fts5_tables()

    def _init_fts5_tables(self):
        """Creates FTS5 virtual table for lightning-fast search across names, events, and places."""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS fts_search_idx USING fts5(
                    entity_id UNINDEXED,
                    entity_type UNINDEXED,
                    title,
                    content,
                    tokenize='unicode61 remove_diacritics 2'
                );
            """))
            conn.commit()

    def get_session(self) -> Session:
        """Returns a new SQLAlchemy Session."""
        return self.session_factory()
