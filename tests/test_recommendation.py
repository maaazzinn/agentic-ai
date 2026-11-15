import unittest
from unittest.mock import patch

from app.services.analyzer import ProblemAnalysis
from app.services.recommendation import generate_recommendations


class SqliteRecommendationTests(unittest.TestCase):
    def setUp(self):
        self.analysis = ProblemAnalysis(
            problem_summary="Need a plumber",
            category="plumbing",
            issue_type="tap_repair",
        )

    def test_returns_matching_sqlite_rows_without_demo_prices_or_availability(self):
        provider = {
            "service_category": "plumbing",
            "shop_name": "SQLite Plumbing",
            "contact_name": "Contact",
            "phone": "+911234",
            "address": "Main Road",
            "area": "Aluva",
            "latitude": None,
            "longitude": None,
            "source_url": "",
            "verification_status": "verified",
        }
        with patch("app.services.recommendation.list_provider_documents", return_value=[provider]) as lookup:
            result = generate_recommendations(self.analysis)

        lookup.assert_called_once_with("plumbing")
        self.assertEqual(result["data_source"], "sqlite")
        self.assertEqual(result["recommended_providers"], [provider | {"name": "SQLite Plumbing", "category": "plumbing", "distance_km": None}])
        self.assertIsNone(result["pricing_estimate"])
        self.assertNotIn("base_visit_charge", result["recommended_providers"][0])

    def test_missing_database_records_do_not_fall_back_to_demo_providers(self):
        with patch("app.services.recommendation.list_provider_documents", return_value=None):
            result = generate_recommendations(self.analysis)

        self.assertEqual(result["recommended_providers"], [])
        self.assertIsNone(result["primary_service"])
        self.assertIn("No plumbing providers", result["notice"])


if __name__ == "__main__":
    unittest.main()
