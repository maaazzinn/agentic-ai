import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services.analyzer import ProblemAnalysis
from app.services.provider_store import list_provider_documents, upsert_provider_records
from app.services.recommendation import generate_recommendations
from scripts.seed_test_booking_data import seed_synthetic_booking_data


class SyntheticBookingDataTests(unittest.TestCase):
    def test_seeded_prices_and_slots_are_available_as_test_data(self):
        record = {
            "service_category": "plumbing",
            "shop_name": "Test Plumbing",
            "area": "Aluva",
        }

        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "providers.sqlite3"
            upsert_provider_records([record], database_path)

            updated_count = seed_synthetic_booking_data(database_path, seed=7)
            with patch(
                "app.services.provider_store.get_provider_database_path",
                return_value=database_path,
            ):
                provider = list_provider_documents("plumbing")[0]
                result = generate_recommendations(
                    ProblemAnalysis(
                        problem_summary="Book a plumber",
                        category="plumbing",
                        issue_type="tap_repair",
                        intent="book",
                    )
                )

        self.assertEqual(updated_count, 1)
        self.assertGreater(provider["base_visit_charge"], 0)
        self.assertGreater(provider["estimated_service_charge"], 0)
        self.assertIn("Today 02:00 PM", provider["slots_available"])
        self.assertEqual(provider["booking_data_source"], "synthetic_test")
        self.assertEqual(
            result["recommended_providers"][0]["booking_data_source"],
            "synthetic_test",
        )
        self.assertIn("Synthetic test prices", result["notice"])
        self.assertIn("no real booking has been placed", result["notice"])


if __name__ == "__main__":
    unittest.main()
