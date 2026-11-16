"""Running queries against a flight database."""

import math

from validator import parse_datetime

RECORD_KEYS = (
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
)
STRING_KEYS = ("flight_id", "origin", "destination")
DATETIME_KEYS = ("departure_datetime", "arrival_datetime")
PRICE_KEYS = ("price", "min_price")
ALLOWED_KEYS = set(RECORD_KEYS) | {"min_price", "sort_by", "order", "limit"}


def _is_number(value) -> bool:
    """A finite int or float; booleans are not numbers."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def _is_valid_query(query) -> bool:
    """Check keys, value types and combinations of a query object."""
    if not isinstance(query, dict):
        return False

    for key, value in query.items():
        if key not in ALLOWED_KEYS:
            return False
        if key in STRING_KEYS:
            if not isinstance(value, str):
                return False
        elif key in DATETIME_KEYS:
            if not isinstance(value, str) or parse_datetime(value) is None:
                return False
        elif key in PRICE_KEYS:
            if not _is_number(value):
                return False
        elif key == "sort_by":
            if not isinstance(value, str) or value not in RECORD_KEYS:
                return False
        elif key == "order":
            if value not in ("asc", "desc"):
                return False
        elif key == "limit":
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                return False

    if "order" in query and "sort_by" not in query:
        return False
    return True


def _matches(record: dict, query: dict) -> bool:
    """True if the record passes every filter condition in the query."""
    for key in STRING_KEYS:
        if key in query and record[key] != query[key]:
            return False
    # 'YYYY-MM-DD HH:MM' strings compare in chronological order.
    if "departure_datetime" in query:
        if record["departure_datetime"] < query["departure_datetime"]:
            return False
    if "arrival_datetime" in query:
        if record["arrival_datetime"] > query["arrival_datetime"]:
            return False
    if "price" in query and not record["price"] <= query["price"]:
        return False
    if "min_price" in query and not record["price"] >= query["min_price"]:
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object."""
    if not _is_valid_query(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    matches = [dict(record) for record in db if _matches(record, query)]

    if "sort_by" in query:
        matches = sorted(
            matches,
            key=lambda record: record[query["sort_by"]],
            reverse=query.get("order", "asc") == "desc",
        )

    if "limit" in query:
        matches = matches[: query["limit"]]

    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list."""
    if isinstance(queries, list):
        return [run_query(db, query) for query in queries]
    return [run_query(db, queries)]
