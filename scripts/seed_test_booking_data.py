"""Add clearly labeled synthetic prices and appointment slots for local testing."""
import argparse
import json
import random
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from app.services.provider_store import get_provider_database_path, initialize_provider_database


PRICE_RANGES = {
    "ac_repair": ((200, 500), (400, 3000)),
    "appliance_repair": ((200, 500), (350, 2500)),
    "car_wash": ((100, 300), (300, 1500)),
    "electrical": ((200, 500), (300, 2500)),
    "home_cleaning": ((250, 750), (1200, 6000)),
    "plumbing": ((150, 450), (250, 1500)),
}
DEFAULT_PRICE_RANGES = ((150, 500), (300, 3000))
SLOT_OPTIONS = (
    "Today 09:00 AM",
    "Today 11:00 AM",
    "Today 02:00 PM",
    "Today 04:00 PM",
    "Tomorrow 10:00 AM",
    "Tomorrow 02:00 PM",
)


def seed_synthetic_booking_data(
    database_path: Optional[Path] = None,
    seed: int = 20261115,
) -> int:
    path = database_path or get_provider_database_path()
    if not path.exists():
        raise FileNotFoundError(f"Provider database not found: {path}")

    generator = random.Random(seed)
    with closing(sqlite3.connect(path)) as connection:
        with connection:
            initialize_provider_database(connection)
            records = connection.execute(
                """
                SELECT service_category, shop_name, phone, booking_data_source
                FROM service_providers
                WHERE booking_data_source IS NULL OR booking_data_source = 'synthetic_test'
                ORDER BY service_category, shop_name, phone
                """
            ).fetchall()
            if not records:
                raise ValueError("No providers need synthetic test prices or appointment slots.")

            for category, shop_name, phone, _ in records:
                visit_range, service_range = PRICE_RANGES.get(category, DEFAULT_PRICE_RANGES)
                visit_charge = generator.randint(*visit_range)
                service_charge = generator.randint(*service_range)
                slots = ["Today 02:00 PM"]
                slots.extend(
                    generator.sample(
                        [slot for slot in SLOT_OPTIONS if slot != "Today 02:00 PM"],
                        k=2,
                    )
                )
                generator.shuffle(slots)
                connection.execute(
                    """
                    UPDATE service_providers
                    SET base_visit_charge = ?,
                        estimated_service_charge = ?,
                        slots_available = ?,
                        booking_data_source = 'synthetic_test'
                    WHERE service_category = ? AND shop_name = ? AND phone = ?
                    """,
                    (
                        visit_charge,
                        service_charge,
                        json.dumps(slots),
                        category,
                        shop_name,
                        phone,
                    ),
                )
    return len(records)


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        help="SQLite database path (defaults to PROVIDER_DATABASE_PATH or local_service_ai.sqlite3)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20261115,
        help="Seed for repeatable pseudo-random test values",
    )
    args = parser.parse_args()

    try:
        updated = seed_synthetic_booking_data(args.database, args.seed)
    except (OSError, sqlite3.Error, ValueError) as exc:
        parser.exit(1, f"Seeding failed: {exc}\n")

    print(f"Added synthetic test prices and appointment slots to {updated} provider records.")
    print("These values are test data only and do not represent provider-confirmed offers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
