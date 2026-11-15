"""Offline reverse geocoding for displaying a nearby place name."""
import io
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import reverse_geocoder


@lru_cache(maxsize=1)
def _geocoder() -> Any:
    gazetteer_path = Path(reverse_geocoder.__file__).with_name("rg_cities1000.csv")
    gazetteer = gazetteer_path.read_text(encoding="utf-8")
    return reverse_geocoder.RGeocoder(
        mode=1,
        verbose=False,
        stream=io.StringIO(gazetteer),
    )


def resolve_place_name(latitude: float, longitude: float) -> Dict[str, str]:
    result = _geocoder().query([(latitude, longitude)])[0]
    place_name = result["name"]
    region = result.get("admin1", "")
    display_name = f"{place_name}, {region}" if region and region.casefold() != place_name.casefold() else place_name
    return {
        "place_name": display_name,
        "city": place_name,
        "region": region,
        "country_code": result.get("cc", ""),
    }
