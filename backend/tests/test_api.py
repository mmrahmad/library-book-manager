import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402


@pytest.fixture
def client(tmp_path):
    app = create_app(database=str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    return app.test_client()


def make_book(client, **overrides):
    payload = {"title": "Dune", "author": "Frank Herbert", "category": "Fiction", "published_year": 1965}
    payload.update(overrides)
    return client.post("/api/books", json=payload)


# ---- Required tests ----

def test_add_book(client):
    res = make_book(client)
    assert res.status_code == 201
    book = res.get_json()
    assert book["id"] > 0
    assert book["title"] == "Dune"
    assert book["is_borrowed"] is False
    assert book["borrower_name"] is None
    assert book["created_at"]

    assert client.get(f"/api/books/{book['id']}").get_json() == book


def test_borrow_same_book_twice_returns_409(client):
    book_id = make_book(client).get_json()["id"]

    first = client.post(f"/api/books/{book_id}/borrow", json={"borrower_name": "Alice"})
    assert first.status_code == 200
    assert first.get_json()["borrower_name"] == "Alice"

    second = client.post(f"/api/books/{book_id}/borrow", json={"borrower_name": "Bob"})
    assert second.status_code == 409
    assert "error" in second.get_json()


@pytest.mark.parametrize("payload, message", [
    ({"author": "X"}, "Title is required"),
    ({"title": "   ", "author": "X"}, "Title is required"),
    ({"title": "X"}, "Author is required"),
    ({"title": "X", "author": "Y", "published_year": 1899}, "between 1900"),
    ({"title": "X", "author": "Y", "published_year": date.today().year + 1}, "between 1900"),
    ({"title": "X", "author": "Y", "published_year": "abc"}, "whole number"),
    ({"title": "X", "author": "Y", "published_year": True}, "whole number"),
    ({"title": 123, "author": "Y"}, "must be a string"),
    (["not", "an", "object"], "JSON object"),
])
def test_invalid_input_returns_400(client, payload, message):
    res = client.post("/api/books", json=payload)
    assert res.status_code == 400
    assert message in res.get_json()["error"]


# ---- Extra coverage ----

def test_malformed_json_returns_400_not_500(client):
    res = client.post("/api/books", data="{bad json", content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"]


def test_borrowed_book_cannot_be_deleted(client):
    book_id = make_book(client).get_json()["id"]
    client.post(f"/api/books/{book_id}/borrow", json={"borrower_name": "Alice"})
    assert client.delete(f"/api/books/{book_id}").status_code == 409

    assert client.post(f"/api/books/{book_id}/return").status_code == 200
    assert client.delete(f"/api/books/{book_id}").status_code == 204
    assert client.get(f"/api/books/{book_id}").status_code == 404


def test_return_when_not_borrowed_returns_409(client):
    book_id = make_book(client).get_json()["id"]
    assert client.post(f"/api/books/{book_id}/return").status_code == 409


def test_borrow_requires_name(client):
    book_id = make_book(client).get_json()["id"]
    res = client.post(f"/api/books/{book_id}/borrow", json={"borrower_name": ""})
    assert res.status_code == 400


def test_not_found_is_json(client):
    for res in (
        client.get("/api/books/999"),
        client.put("/api/books/999", json={"title": "X", "author": "Y"}),
        client.delete("/api/books/999"),
        client.post("/api/books/999/borrow", json={"borrower_name": "A"}),
        client.post("/api/books/999/return"),
        client.get("/api/books/99999999999999999999999"),
        client.get("/api/nope"),
    ):
        assert res.status_code == 404
        assert "error" in res.get_json()


def test_update_book(client):
    book_id = make_book(client).get_json()["id"]
    res = client.put(f"/api/books/{book_id}", json={"title": "Dune Messiah", "author": "Frank Herbert",
                                                    "published_year": 1969})
    assert res.status_code == 200
    assert res.get_json()["title"] == "Dune Messiah"
    assert client.put(f"/api/books/{book_id}", json={"title": ""}).status_code == 400


def test_search_filter_sort_and_paginate(client):
    make_book(client, title="Cosmos", author="Carl Sagan", category="Science")
    make_book(client, title="Sapiens", author="Yuval Harari", category="History")
    make_book(client, title="100% Real", author="Someone", category="Fiction")

    assert [b["title"] for b in client.get("/api/books?search=sagan").get_json()["items"]] == ["Cosmos"]
    assert [b["title"] for b in client.get("/api/books?search=%25").get_json()["items"]] == ["100% Real"]
    assert client.get("/api/books?category=history").get_json()["total"] == 1

    res = client.get("/api/books?sort=title&order=asc&per_page=2&page=2").get_json()
    assert res["total"] == 3 and res["pages"] == 2
    assert [b["title"] for b in res["items"]] == ["Sapiens"]

    assert client.get("/api/books?sort=drop_table").status_code == 400
    assert client.get("/api/books?page=0").status_code == 400
