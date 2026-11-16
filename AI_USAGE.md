# AI usage disclosure

## Tools used

- Claude (Anthropic), via the claude.ai chat interface.
- Conversation link: (https://claude.ai/share/fa1f5452-8e64-45bd-95df-4159ed91d23a)

## What I used it for

- Planning the order of work (validator, CSV loader, queries, entry point).
- Writing the first version of the code for each module.
- Explaining the checks that are easy to get wrong (ASCII-only matching, strict date format, `argparse` exit codes, `logging` handler cleanup).

## Which parts were AI-generated or substantially AI-assisted

- `validator.py`: `load_airports`, `parse_datetime`, `validate_row`, `to_record`
- `csv_loader.py`: `parse_files`
- `query.py`: `run_query`, `run_queries`, query validation helpers
- `flight_parser.py`: `build_parser`, `main`, `write_error_log`, file output helpers

## Key prompts

1. "Tell me in order what to do and send the tasks one by one, each task separately" (the task description was attached).
2. "Show the code of every file in a window on the right, one file at a time."
3. I pasted the output of my test commands after each file and asked what to do next.

## What I changed or verified myself

I copied each file into my repository and ran it on the sample data (`data/db.csv`, `data/query.json`), comparing the 12 error codes and the 5 query results with the worked example in the assignment, and I ran the public test script before submitting.