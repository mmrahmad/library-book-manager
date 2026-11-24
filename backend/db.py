"""SQLite helpers: one connection per request, schema creation."""
import os
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    title          TEXT    NOT NULL,
    author         TEXT    NOT NULL,
    category       TEXT,
    published_year INTEGER,
    is_borrowed    INTEGER NOT NULL DEFAULT 0,
    borrower_name  TEXT,
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
"""

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(path):
    with connect(path) as conn:
        conn.executescript(SCHEMA)


def row_to_book(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "author": row["author"],
        "category": row["category"],
        "published_year": row["published_year"],
        "is_borrowed": bool(row["is_borrowed"]),
        "borrower_name": row["borrower_name"],
        "created_at": row["created_at"],
    }
