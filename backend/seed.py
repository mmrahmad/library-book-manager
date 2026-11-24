"""Seed the database with 10 sample books.

Usage: python seed.py            # add samples (skips if books already exist)
       python seed.py --reset    # wipe the table first
"""
import os
import sys

from db import DEFAULT_DB_PATH, connect, init_db

BOOKS = [
    ("To Kill a Mockingbird", "Harper Lee", "Fiction", 1960),
    ("1984", "George Orwell", "Fiction", 1949),
    ("The Great Gatsby", "F. Scott Fitzgerald", "Fiction", 1925),
    ("One Hundred Years of Solitude", "Gabriel García Márquez", "Fiction", 1967),
    ("A Brief History of Time", "Stephen Hawking", "Science", 1988),
    ("The Selfish Gene", "Richard Dawkins", "Science", 1976),
    ("Cosmos", "Carl Sagan", "Science", 1980),
    ("Sapiens: A Brief History of Humankind", "Yuval Noah Harari", "History", 2011),
    ("Guns, Germs, and Steel", "Jared Diamond", "History", 1997),
    ("The Diary of a Young Girl", "Anne Frank", "History", 1947),
]


def seed(path, reset=False):
    init_db(path)
    with connect(path) as conn:
        if reset:
            conn.execute("DELETE FROM books")
            conn.execute("DELETE FROM sqlite_sequence WHERE name = 'books'")
        elif conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] > 0:
            print("Books already present; use --reset to start over.")
            return
        conn.executemany(
            "INSERT INTO books (title, author, category, published_year) VALUES (?, ?, ?, ?)",
            BOOKS,
        )
        # Borrow one sample so both badge states are visible right away.
        conn.execute("UPDATE books SET is_borrowed = 1, borrower_name = 'Alice' WHERE title = '1984'")
    print(f"Seeded {len(BOOKS)} books into {path}")


if __name__ == "__main__":
    seed(os.environ.get("LIBRARY_DB", DEFAULT_DB_PATH), reset="--reset" in sys.argv)
