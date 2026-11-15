import unittest

from services.location_resolver import resolve_place_name


class LocationResolverTests(unittest.TestCase):
    def test_resolves_nearby_city_and_region_from_offline_data(self):
        place = resolve_place_name(9.93988, 76.26022)

        self.assertTrue(place["city"])
        self.assertEqual(place["region"], "Kerala")
        self.assertEqual(place["country_code"], "IN")
        self.assertIn(place["city"], place["place_name"])


if __name__ == "__main__":
    unittest.main()
