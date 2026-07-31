"""Checkpointer selection.

The reference implementation required a Postgres connection at import time, so the
app couldn't even start without a database. Here Postgres is opt-in: set
DATABASE_URL to persist threads across restarts, otherwise trips are checkpointed
in memory for the life of the process.
"""

from functools import lru_cache

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from app.config import get_settings


@lru_cache
def get_checkpointer() -> BaseCheckpointSaver:
    settings = get_settings()

    if not settings.database_url:
        return MemorySaver()

    import psycopg
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg.rows import dict_row

    database_url = settings.database_url
    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"

    conn = psycopg.connect(database_url, autocommit=True, row_factory=dict_row)
    saver = PostgresSaver(conn)
    saver.setup()
    return saver
