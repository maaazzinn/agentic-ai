"""Import provider-directory rows from CSV into SQLite."""
import argparse
import sqlite3
import sys

from dotenv import load_dotenv

from services.provider_store import parse_provider_csv, upsert_provider_records


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, help="Path to the provider CSV file")
    parser.add_argument(
        "--database",
        help="SQLite database path (defaults to PROVIDER_DATABASE_PATH or local_service_ai.sqlite3)",
    )
    args = parser.parse_args()

    try:
        records = parse_provider_csv(args.csv)
        imported = upsert_provider_records(records, args.database)
    except (OSError, ValueError) as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1
    except sqlite3.Error as exc:
        print(f"SQLite import failed: {exc}", file=sys.stderr)
        return 1

    print(f"Processed {imported} provider records into SQLite.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
