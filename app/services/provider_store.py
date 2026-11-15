"""SQLite storage and CSV validation for the local provider directory."""
import csv
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


REQUIRED_PROVIDER_FIELDS = (
    "service_category",
    "shop_name",
    "contact_name",
    "phone",
    "address",
    "area",
    "latitude",
    "longitude",
    "source_url",
    "verification_status",
)
PROVIDER_FIELDS = REQUIRED_PROVIDER_FIELDS + (
    "base_visit_charge",
    "estimated_service_charge",
    "slots_available",
    "booking_data_source",
)


class ServiceProviderRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    service_category: str = Field(min_length=1)
    shop_name: str = Field(min_length=1)
    contact_name: str = ""
    phone: str = ""
    address: str = ""
    area: str = Field(min_length=1)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    source_url: str = ""
    verification_status: str = "unverified"
    base_visit_charge: Optional[int] = Field(default=None, ge=0)
    estimated_service_charge: Optional[int] = Field(default=None, ge=0)
    slots_available: List[str] = Field(default_factory=list)
    booking_data_source: Optional[str] = None

    @field_validator(
        "service_category",
        "shop_name",
        "contact_name",
        "phone",
        "address",
        "area",
        "source_url",
        "verification_status",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("service_category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        return value.lower().replace("-", "_").replace(" ", "_")

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def empty_coordinates_are_missing(cls, value: Any) -> Any:
        return None if value is None or (isinstance(value, str) and not value.strip()) else value

    @field_validator("base_visit_charge", "estimated_service_charge", mode="before")
    @classmethod
    def empty_charges_are_missing(cls, value: Any) -> Any:
        return None if value is None or (isinstance(value, str) and not value.strip()) else value

    @field_validator("slots_available", mode="before")
    @classmethod
    def parse_slots(cls, value: Any) -> List[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = value.split("|")
        if not isinstance(value, list):
            raise ValueError("slots_available must be a list or a JSON array")
        return [str(slot).strip() for slot in value if str(slot).strip()]

    @field_validator("booking_data_source", mode="before")
    @classmethod
    def normalize_booking_data_source(cls, value: Any) -> Optional[str]:
        normalized = str(value).strip() if value is not None else ""
        if not normalized:
            return None
        if normalized not in {"provider_supplied", "synthetic_test"}:
            raise ValueError("booking_data_source must be provider_supplied or synthetic_test")
        return normalized


def parse_provider_csv(path: str) -> List[Dict[str, Any]]:
    """Read and validate provider rows from a CSV with the expected columns."""
    with Path(path).open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("CSV file is missing its header row.")

        missing_fields = [field for field in REQUIRED_PROVIDER_FIELDS if field not in reader.fieldnames]
        if missing_fields:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing_fields)}")

        records = []
        for line_number, row in enumerate(reader, start=2):
            try:
                records.append(ServiceProviderRecord.model_validate(row).model_dump())
            except ValidationError as exc:
                raise ValueError(f"Invalid provider data on CSV line {line_number}: {exc}") from exc
    return records


def get_provider_database_path() -> Path:
    return Path(os.getenv("PROVIDER_DATABASE_PATH", "local_service_ai.sqlite3"))


def initialize_provider_database(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS service_providers (
            service_category TEXT NOT NULL,
            shop_name TEXT NOT NULL,
            contact_name TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            area TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            source_url TEXT NOT NULL DEFAULT '',
            verification_status TEXT NOT NULL DEFAULT 'unverified',
            base_visit_charge INTEGER CHECK (base_visit_charge IS NULL OR base_visit_charge >= 0),
            estimated_service_charge INTEGER CHECK (estimated_service_charge IS NULL OR estimated_service_charge >= 0),
            slots_available TEXT NOT NULL DEFAULT '[]',
            booking_data_source TEXT,
            UNIQUE (service_category, shop_name, phone),
            CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
            CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180)
        )
        """
    )
    existing_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(service_providers)")
    }
    new_columns = {
        "base_visit_charge": "INTEGER",
        "estimated_service_charge": "INTEGER",
        "slots_available": "TEXT NOT NULL DEFAULT '[]'",
        "booking_data_source": "TEXT",
    }
    for column, definition in new_columns.items():
        if column not in existing_columns:
            connection.execute(
                f"ALTER TABLE service_providers ADD COLUMN {column} {definition}"
            )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_service_providers_category ON service_providers(service_category)"
    )


def list_provider_documents(category: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """List SQLite provider records, or None when the database has not been imported yet."""
    database_path = get_provider_database_path()
    if not database_path.exists():
        return None

    query = "SELECT " + ", ".join(PROVIDER_FIELDS) + " FROM service_providers"
    parameters = ()
    if category:
        query += " WHERE service_category = ?"
        parameters = (category.lower().replace("-", "_").replace(" ", "_"),)
    query += " ORDER BY shop_name COLLATE NOCASE"

    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        with connection:
            initialize_provider_database(connection)
            records = [dict(row) for row in connection.execute(query, parameters).fetchall()]
            for record in records:
                record["slots_available"] = json.loads(record["slots_available"])
            return records


def upsert_provider_records(
    records: List[Dict[str, Any]],
    database_path: Optional[str] = None,
) -> int:
    """Create the provider table if needed and insert or update CSV records."""
    path = Path(database_path) if database_path else get_provider_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ", ".join(PROVIDER_FIELDS)
    placeholders = ", ".join("?" for _ in PROVIDER_FIELDS)
    update_columns = ", ".join(
        f"{field} = excluded.{field}"
        for field in PROVIDER_FIELDS
        if field not in ("service_category", "shop_name", "phone")
    )
    sql = (
        f"INSERT INTO service_providers ({columns}) VALUES ({placeholders}) "
        "ON CONFLICT (service_category, shop_name, phone) "
        f"DO UPDATE SET {update_columns}"
    )

    normalized_records = [
        ServiceProviderRecord.model_validate(record).model_dump()
        for record in records
    ]
    for record in normalized_records:
        record["slots_available"] = json.dumps(record["slots_available"])

    with closing(sqlite3.connect(path)) as connection:
        with connection:
            initialize_provider_database(connection)
            connection.executemany(
                sql,
                [tuple(record[field] for field in PROVIDER_FIELDS) for record in normalized_records],
            )
    return len(records)
