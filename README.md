# Library Book Manager

A small web app where a librarian can manage books and track who has borrowed them.

- **Backend:** Python Flask + SQLite (`backend/`)
- **Frontend:** AngularJS 1.8 + ngRoute + Bootstrap 5 (`frontend/`)

## Requirements

- Python 3.10+
- Node.js 18+ (only used to install AngularJS/Bootstrap and serve static files)

## Quick start

Open two terminals.

**1. Backend** (http://localhost:5001)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                     # adds 10 sample books (use --reset to start over)
python app.py
```

**2. Frontend** (http://localhost:8080)

```bash
cd frontend
npm install
npm start
```

Then open **http://localhost:8080/#!/books**.

> Port 5001 is used instead of Flask's default 5000 because macOS uses 5000 for AirPlay.
> To point the frontend at a different API, edit `frontend/app/config.js`.
> The backend reads `PORT` and `LIBRARY_DB` (SQLite file path) from the environment.

### Run the tests

```bash
cd backend
source .venv/bin/activate
pytest -v
```

### Docker Compose (optional)

```bash
docker compose up --build
```

Frontend on http://localhost:8080, API on http://localhost:5001. The database is seeded
on first start and kept in a named volume.

## Project layout

```
backend/
  app.py            Flask app factory, routes, JSON error handlers
  db.py             SQLite connection per request, schema, row -> dict
  validation.py     Input validation for books and borrowing
  seed.py           Seeds 10 sample books
  tests/test_api.py pytest suite (18 tests)
frontend/
  index.html
  app/
    config.js                 API base URL
    app.module.js             Module + ngRoute routes
    book.service.js           BookService: every HTTP call lives here
    book-list.controller.js   List, search, filter, sort, paginate, borrow/return/delete
    book-form.controller.js   Add / edit form
    views/                    Templates
```

## API

All responses are JSON, including errors (`{"error": "Title is required"}`).

| Method | Path                        | Purpose                                   | Responses               |
| ------ | --------------------------- | ----------------------------------------- | ----------------------- |
| GET    | `/api/books`                | List books (see query params below)       | 200; 400 on bad params  |
| POST   | `/api/books`                | Add a book                                | 201; 400                |
| GET    | `/api/books/<id>`           | One book                                  | 200; 404                |
| PUT    | `/api/books/<id>`           | Edit a book                               | 200; 400; 404           |
| DELETE | `/api/books/<id>`           | Delete a book                             | 204; 404; 409 if borrowed |
| POST   | `/api/books/<id>/borrow`    | Borrow; body `{"borrower_name": "..."}`   | 200; 400; 404; 409      |
| POST   | `/api/books/<id>/return`    | Return                                    | 200; 404; 409           |
| GET    | `/api/categories`           | Distinct categories (for the filter)      | 200                     |
| GET    | `/api/health`               | Health check                              | 200                     |

`GET /api/books` query parameters (all optional):

- `search` – case-insensitive match on title or author
- `category` – exact category (case-insensitive)
- `sort` – `title`, `author`, `category`, `published_year`, `created_at` (default)
- `order` – `asc` or `desc` (default)
- `page` (default 1), `per_page` (default 10, max 100)

Response: `{"items": [...], "total": 10, "page": 1, "per_page": 10, "pages": 1}`

A book: `id, title, author, category, published_year, is_borrowed, borrower_name, created_at`.

### Business rules

- Title and author are required (whitespace-only is rejected); published year, if given,
  must be a whole number between 1900 and the current year.
- Borrowing an already-borrowed book returns **409**. The check is part of the `UPDATE ... WHERE
  is_borrowed = 0` statement, so two simultaneous requests cannot both succeed.
- Deleting a borrowed book returns **409** (same atomic pattern). Returning a book that is not
  borrowed returns **409**.
- Bad input never causes a 500: malformed JSON, non-object bodies, wrong types, huge IDs and
  unknown routes/methods all return a JSON 4xx.

## Design notes

- **App factory** (`create_app(database=...)`) so tests run against a fresh temp SQLite file.
- **Validation** is in its own module and returns the first error message, which the UI shows as-is.
- **Frontend**: `controllerAs: 'vm'`; controllers never call `$http` directly. `BookService`
  turns every failure into a readable message (including "cannot reach the server").
  Forms use AngularJS validation (`required`, `min`/`max`, `maxlength`) for inline errors; the
  server validates again. The borrow dialog asks for the borrower's name before borrowing.
  The search box is debounced (300 ms). On phones, the author/category/year columns fold
  under the title so the table has no horizontal scroll.
- **Bonus:** server-side sorting and pagination, Docker Compose.

## What I would improve with more time

- Frontend unit tests (Karma/Jasmine with `angular-mocks` for `BookService` and the controllers)
  and an end-to-end test in CI.
- A borrowing history table (who borrowed what and when, due dates) instead of a single
  `borrower_name` column.
- Database migrations (e.g. Alembic) instead of `CREATE TABLE IF NOT EXISTS`.
- Authentication for librarians, and restricting CORS to the real frontend origin.
- Return field-level error objects from the API (e.g. `{"errors": {"title": "..."}}`) so the
  form can highlight the exact field the server rejected.
- Optimistic concurrency on edits (e.g. an `updated_at` check) to avoid lost updates.

## Use of AI tools

This project was built with the help of an AI coding assistant (Claude Code). I used it to
scaffold the backend, frontend, tests, Docker setup and this README, and to run a headless
browser check of the main user flows. I reviewed the code and can explain and change every part of it.
