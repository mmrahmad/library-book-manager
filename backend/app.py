"""Library Book Manager - Flask JSON API."""
import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from db import DEFAULT_DB_PATH, close_db, get_db, init_db, row_to_book
from validation import validate_book, validate_borrow

SORTABLE_FIELDS = {"title", "author", "category", "published_year", "created_at"}
MAX_PER_PAGE = 100
SQLITE_MAX_INT = 2**63 - 1


def error(message, status):
    return jsonify({"error": message}), status


def create_app(database=None):
    app = Flask(__name__)
    app.config["DATABASE"] = database or os.environ.get("LIBRARY_DB", DEFAULT_DB_PATH)
    app.json.sort_keys = False

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    init_db(app.config["DATABASE"])
    app.teardown_appcontext(close_db)

    # ---- Error handlers: every response, including errors, is JSON ----

    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        return error(exc.description or exc.name, exc.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        app.logger.exception("Unhandled error")
        return error("Internal server error", 500)

    # ---- Helpers ----

    def find_book(book_id):
        if book_id > SQLITE_MAX_INT:
            return None
        return get_db().execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()

    def json_body():
        # silent=True: malformed JSON returns None instead of raising,
        # so the validator can answer with a clear 400 message.
        return request.get_json(silent=True)

    def parse_positive_int(name, default):
        raw = request.args.get(name)
        if raw is None or raw == "":
            return default, None
        if not raw.isdigit() or int(raw) < 1:
            return None, f"'{name}' must be a positive integer"
        return int(raw), None

    # ---- Routes ----

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/books")
    def list_books():
        search = request.args.get("search", "").strip()
        category = request.args.get("category", "").strip()
        sort = request.args.get("sort", "created_at")
        order = request.args.get("order", "desc").lower()

        if sort not in SORTABLE_FIELDS:
            return error(f"'sort' must be one of: {', '.join(sorted(SORTABLE_FIELDS))}", 400)
        if order not in ("asc", "desc"):
            return error("'order' must be 'asc' or 'desc'", 400)
        page, err = parse_positive_int("page", 1)
        if err:
            return error(err, 400)
        per_page, err = parse_positive_int("per_page", 10)
        if err:
            return error(err, 400)
        per_page = min(per_page, MAX_PER_PAGE)

        where, params = [], []
        if search:
            # Escape LIKE wildcards so "%" or "_" in a search match literally.
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            where.append("(title LIKE ? ESCAPE '\\' OR author LIKE ? ESCAPE '\\')")
            params += [f"%{escaped}%", f"%{escaped}%"]
        if category:
            where.append("category = ? COLLATE NOCASE")
            params.append(category)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        db = get_db()
        total = db.execute(f"SELECT COUNT(*) FROM books {where_sql}", params).fetchone()[0]
        # `sort` and `order` are whitelisted above, so interpolating them is safe.
        collate = " COLLATE NOCASE" if sort in ("title", "author", "category") else ""
        rows = db.execute(
            f"SELECT * FROM books {where_sql} "
            f"ORDER BY {sort}{collate} {order}, id {order} LIMIT ? OFFSET ?",
            params + [per_page, (page - 1) * per_page],
        ).fetchall()

        return jsonify({
            "items": [row_to_book(r) for r in rows],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        })

    @app.get("/api/categories")
    def list_categories():
        rows = get_db().execute(
            "SELECT DISTINCT category FROM books WHERE category IS NOT NULL "
            "ORDER BY category COLLATE NOCASE"
        ).fetchall()
        return jsonify([r["category"] for r in rows])

    @app.post("/api/books")
    def create_book():
        data, err = validate_book(json_body())
        if err:
            return error(err, 400)
        db = get_db()
        cur = db.execute(
            "INSERT INTO books (title, author, category, published_year) VALUES (?, ?, ?, ?)",
            (data["title"], data["author"], data["category"], data["published_year"]),
        )
        db.commit()
        return jsonify(row_to_book(find_book(cur.lastrowid))), 201

    @app.get("/api/books/<int:book_id>")
    def get_book(book_id):
        row = find_book(book_id)
        if row is None:
            return error("Book not found", 404)
        return jsonify(row_to_book(row))

    @app.put("/api/books/<int:book_id>")
    def update_book(book_id):
        if find_book(book_id) is None:
            return error("Book not found", 404)
        data, err = validate_book(json_body())
        if err:
            return error(err, 400)
        db = get_db()
        db.execute(
            "UPDATE books SET title = ?, author = ?, category = ?, published_year = ? WHERE id = ?",
            (data["title"], data["author"], data["category"], data["published_year"], book_id),
        )
        db.commit()
        return jsonify(row_to_book(find_book(book_id)))

    @app.delete("/api/books/<int:book_id>")
    def delete_book(book_id):
        row = find_book(book_id)
        if row is None:
            return error("Book not found", 404)
        db = get_db()
        # The is_borrowed condition makes the check-and-delete atomic.
        cur = db.execute("DELETE FROM books WHERE id = ? AND is_borrowed = 0", (book_id,))
        db.commit()
        if cur.rowcount == 0:
            return error("Book is currently borrowed and cannot be deleted until it is returned", 409)
        return "", 204

    @app.post("/api/books/<int:book_id>/borrow")
    def borrow_book(book_id):
        if find_book(book_id) is None:
            return error("Book not found", 404)
        name, err = validate_borrow(json_body())
        if err:
            return error(err, 400)
        db = get_db()
        cur = db.execute(
            "UPDATE books SET is_borrowed = 1, borrower_name = ? WHERE id = ? AND is_borrowed = 0",
            (name, book_id),
        )
        db.commit()
        if cur.rowcount == 0:
            return error("Book is already borrowed", 409)
        return jsonify(row_to_book(find_book(book_id)))

    @app.post("/api/books/<int:book_id>/return")
    def return_book(book_id):
        if find_book(book_id) is None:
            return error("Book not found", 404)
        db = get_db()
        cur = db.execute(
            "UPDATE books SET is_borrowed = 0, borrower_name = NULL WHERE id = ? AND is_borrowed = 1",
            (book_id,),
        )
        db.commit()
        if cur.rowcount == 0:
            return error("Book is not currently borrowed", 409)
        return jsonify(row_to_book(find_book(book_id)))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=True)
