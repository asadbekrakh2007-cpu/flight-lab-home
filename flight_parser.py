"""Flight schedule parser and query tool (command-line entry point)."""

import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "251adb073"
FIRST_NAME = "Asadbek"
LAST_NAME = "Rakhmatillaev"


class DataError(Exception):
    """A runtime problem with the shape or content of an input file."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flight_parser.py",
        description="Validate flight CSV files, store them as a JSON "
                    "database and answer queries against it.",
        allow_abbrev=False,
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE", help="parse a single CSV file")
    source.add_argument("-d", metavar="FOLDER",
                        help="parse every .csv file in a folder")
    source.add_argument("-j", metavar="FILE",
                        help="load an existing JSON database")
    parser.add_argument("-a", metavar="FILE",
                        help="airport list file (required with -i and -d)")
    parser.add_argument("-o", metavar="FILE",
                        help="output path for the JSON database "
                             "(default: db.json)")
    parser.add_argument("-q", metavar="FILE", help="JSON file with queries")
    parser.add_argument("-r", metavar="FOLDER", default=".",
                        help="folder for the response file "
                             "(default: current directory)")
    return parser


def parse_arguments(argv):
    """Parse and check the command line; usage errors exit with code 2."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.j is None and args.a is None:
        parser.error("-a is required with -i and -d")
    if args.j is not None and args.o is not None:
        parser.error("-o cannot be used with -j")
    return args


def load_json(path: str):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def load_database(path: str) -> list[dict]:
    db = load_json(path)
    if not isinstance(db, list) or not all(isinstance(r, dict) for r in db):
        raise DataError(f"{path}: database must be a JSON array of objects")
    return db


def load_queries(path: str):
    queries = load_json(path)
    if not isinstance(queries, (dict, list)):
        raise DataError(
            f"{path}: queries must be a JSON object or an array of objects")
    return queries


def find_csv_files(folder: str) -> list[str]:
    if not os.path.isdir(folder):
        raise DataError(f"{folder}: folder does not exist")
    names = sorted(
        name for name in os.listdir(folder)
        if name.endswith(".csv") and os.path.isfile(os.path.join(folder, name))
    )
    if not names:
        raise DataError(f"{folder}: no .csv files found")
    return [os.path.join(folder, name) for name in names]


def write_error_log(log_path: str, errors: list[str], n_valid: int) -> None:
    """Write errors.log with the logging module and always clean up."""
    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    try:
        logger.info("%d valid rows, %d invalid rows", n_valid, len(errors))
        for message in errors:
            logger.warning(message)
    finally:
        logger.removeHandler(handler)
        handler.close()


def write_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def response_path(folder: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"
    return os.path.join(folder, name)


def run(args) -> None:
    # Read the query file first, so a bad one fails before anything is written.
    queries = load_queries(args.q) if args.q is not None else None

    if args.j is not None:
        db = load_database(args.j)
    else:
        airports = load_airports(args.a)
        paths = [args.i] if args.i is not None else find_csv_files(args.d)
        db, errors = parse_files(paths, airports)

        db_path = args.o if args.o is not None else "db.json"
        log_path = os.path.join(
            os.path.dirname(os.path.abspath(db_path)), "errors.log")
        write_error_log(log_path, errors, len(db))
        write_json(db_path, db)
        print(f"Valid rows: {len(db)}, invalid rows: {len(errors)}")

    if queries is not None:
        entries = run_queries(db, queries)
        out_path = response_path(args.r)
        write_json(out_path, entries)
        print(f"Responses written to {out_path}")


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_arguments(argv)
    except SystemExit as exc:  # argparse: -h gives 0, usage errors give 2
        return exc.code if isinstance(exc.code, int) else 1

    try:
        run(args)
    except (OSError, ValueError, DataError) as exc:
        message = " ".join(str(exc).split())
        print(f"Error: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())