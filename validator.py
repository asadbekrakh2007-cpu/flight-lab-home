"""Validation of single flight rows."""

import math
import re
from datetime import datetime

FLIGHT_ID_RE = re.compile(r"[A-Za-z0-9]{2,8}")
AIRPORT_RE = re.compile(r"[A-Z]{3}")
# [0-9] (not \d) so that non-ASCII digits are rejected.
DATETIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def load_airports(path: str) -> set[str]:
    """Read an airport list file and return the set of codes."""
    airports = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            code = line.strip()
            if not code or code.startswith("#"):
                continue
            airports.add(code)
    return airports


def parse_datetime(text: str):
    """Return a datetime for 'YYYY-MM-DD HH:MM' (strict format), else None."""
    if not DATETIME_RE.fullmatch(text):
        return None
    try:
        return datetime.strptime(text, DATETIME_FORMAT)
    except ValueError:
        return None


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Return None if the row is valid, else the first failing error code."""
    # 1. field count
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"

    flight_id, origin, destination, dep, arr, price = (
        field.strip() for field in fields
    )

    # 2. empty fields
    if not all((flight_id, origin, destination, dep, arr, price)):
        return "MISSING_FIELD"

    # 3. flight id
    if not FLIGHT_ID_RE.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"

    # 4. origin
    if not AIRPORT_RE.fullmatch(origin) or origin not in airports:
        return "INVALID_ORIGIN"

    # 5. destination
    if not AIRPORT_RE.fullmatch(destination) or destination not in airports:
        return "INVALID_DESTINATION"

    # 6. same origin and destination
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    # 7. departure
    dep_dt = parse_datetime(dep)
    if dep_dt is None:
        return "INVALID_DEPARTURE"

    # 8. arrival
    arr_dt = parse_datetime(arr)
    if arr_dt is None:
        return "INVALID_ARRIVAL"

    # 9. arrival must be after departure
    if arr_dt <= dep_dt:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    # 10. price must be a finite number
    try:
        price_value = float(price)
    except ValueError:
        return "INVALID_PRICE"
    if not math.isfinite(price_value):
        return "INVALID_PRICE"

    # 11. price must be positive
    if price_value <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary."""
    flight_id, origin, destination, dep, arr, price = (
        field.strip() for field in fields
    )
    return {
        "flight_id": flight_id,
        "origin": origin,
        "destination": destination,
        "departure_datetime": dep,
        "arrival_datetime": arr,
        "price": float(price),
    }
