import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from app.services.provider_store import (
    PROVIDER_FIELDS,
    ServiceProviderRecord,
    list_provider_documents,
    parse_provider_csv,
    upsert_provider_records,
)


class ProviderRecordTests(unittest.TestCase):
    def test_normalizes_category_and_keeps_coordinates_numeric(self):
        record = ServiceProviderRecord.model_validate({
            "service_category": "Home Cleaning",
            "shop_name": "Clean House",
            "area": "Aluva",
            "latitude": "10.10",
            "longitude": "76.35",
        })

        self.assertEqual(record.service_category, "home_cleaning")
        self.assertEqual(record.latitude, 10.1)
        self.assertEqual(record.longitude, 76.35)
        self.assertEqual(record.phone, "")

    def test_rejects_out_of_range_coordinates(self):
        with self.assertRaises(ValidationError):
            ServiceProviderRecord.model_validate({
                "service_category": "plumbing",
                "shop_name": "A Plumber",
                "area": "Aluva",
                "latitude": 100,
                "longitude": 76.35,
            })

    def test_allows_missing_coordinates(self):
        record = ServiceProviderRecord.model_validate({
            "service_category": "plumbing",
            "shop_name": "A Plumber",
            "area": "Aluva",
            "latitude": "",
            "longitude": "",
        })

        self.assertIsNone(record.latitude)
        self.assertIsNone(record.longitude)

    def test_csv_requires_expected_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "providers.csv"
            csv_path.write_text("shop_name,area\nClean House,Aluva\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing required columns"):
                parse_provider_csv(str(csv_path))

    def test_csv_parses_provider_records(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "providers.csv"
            csv_path.write_text(
                ",".join(PROVIDER_FIELDS)
                + "\nplumbing,Good Plumber,Sam,+911234,Main Rd,Aluva,10.1,76.35,https://example.com,verified\n",
                encoding="utf-8",
            )

            records = parse_provider_csv(str(csv_path))

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["service_category"], "plumbing")
        self.assertEqual(records[0]["latitude"], 10.1)
        self.assertEqual(records[0]["phone"], "+911234")

    def test_imports_and_lists_sqlite_records_idempotently(self):
        record = ServiceProviderRecord.model_validate({
            "service_category": "Home Cleaning",
            "shop_name": "Clean House",
            "area": "Aluva",
        }).model_dump()

        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "providers.sqlite3"
            self.assertEqual(upsert_provider_records([record], database_path), 1)
            self.assertEqual(upsert_provider_records([record], database_path), 1)

            with patch("app.services.provider_store.get_provider_database_path", return_value=database_path):
                records = list_provider_documents("Home Cleaning")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["service_category"], "home_cleaning")
        self.assertEqual(records[0]["shop_name"], "Clean House")
        self.assertIsNone(records[0]["latitude"])
if __name__ == "__main__":
    unittest.main()
