"""Reading CSV files into flight records and error messages."""

import csv
import os

from validator import to_record, validate_row


def _read_lines(path: str) -> list[str]:
    """Return the physical lines of a file without line endings.

    Lines end in \\n or \\r\\n; a trailing \\r is removed.
    """
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()  # file ended with a newline
    return [line[:-1] if line.endswith("\r") else line for line in lines]


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Process the CSV files in the order given.

    Return (records, errors):
      records - valid flight records, in input order
      errors  - one message per invalid row, in input order, formatted as
                "<file name>:<line number>: <ERROR_CODE> | <free text>"
                (base file name only, no timestamp or level, no newline)

    Also performs the DUPLICATE_FLIGHT check across all the files.
    Does not write any files and does not log anything itself.
    """
    records: list[dict] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    for path in paths:
        file_name = os.path.basename(path)
        lines = _read_lines(path)

        for line_number, line in enumerate(lines, start=1):
            if line_number == 1:
                continue  # header
            if line.strip() == "":
                continue  # blank line
            if line.lstrip().startswith("#"):
                continue  # comment line

            try:
                fields = next(csv.reader([line]), [])
            except csv.Error:
                fields = [line]

            code = validate_row(fields, airports)
            if code is None:
                record = to_record(fields)
                key = (record["flight_id"], record["departure_datetime"])
                if key in seen:
                    code = "DUPLICATE_FLIGHT"
                else:
                    seen.add(key)
                    records.append(record)

            if code is not None:
                errors.append(f"{file_name}:{line_number}: {code} | {line}")

    return records, errors
