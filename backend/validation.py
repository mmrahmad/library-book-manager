"""Input validation. Each function returns (clean_data, error_message)."""
from datetime import date

MIN_YEAR = 1900
MAX_TITLE = 200
MAX_AUTHOR = 120
MAX_CATEGORY = 50
MAX_BORROWER = 100


def _clean_str(data, field, label, max_len, required):
    value = data.get(field)
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, (f"{label} is required" if required else None)
    if not isinstance(value, str):
        return None, f"{label} must be a string"
    value = value.strip()
    if len(value) > max_len:
        return None, f"{label} must be at most {max_len} characters"
    return value, None


def _clean_year(value):
    if value is None or value == "":
        return None, None
    # bool is a subclass of int in Python, so reject it explicitly.
    if isinstance(value, bool):
        return None, "Published year must be a whole number"
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value.strip())
    elif isinstance(value, float) and value.is_integer():
        value = int(value)
    if not isinstance(value, int):
        return None, "Published year must be a whole number"
    current_year = date.today().year
    if not MIN_YEAR <= value <= current_year:
        return None, f"Published year must be between {MIN_YEAR} and {current_year}"
    return value, None


def validate_book(data):
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object"

    title, err = _clean_str(data, "title", "Title", MAX_TITLE, required=True)
    if err:
        return None, err
    author, err = _clean_str(data, "author", "Author", MAX_AUTHOR, required=True)
    if err:
        return None, err
    category, err = _clean_str(data, "category", "Category", MAX_CATEGORY, required=False)
    if err:
        return None, err
    year, err = _clean_year(data.get("published_year"))
    if err:
        return None, err

    return {"title": title, "author": author, "category": category, "published_year": year}, None


def validate_borrow(data):
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object"
    name, err = _clean_str(data, "borrower_name", "Borrower name", MAX_BORROWER, required=True)
    if err:
        return None, err
    return name, None
