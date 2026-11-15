"""
SQLite-backed service directory lookup for Local Service AI.
"""
from typing import Any, Dict, List, Optional

from .analyzer import ProblemAnalysis
from .mcp_catalog import haversine_distance_km
from .provider_store import list_provider_documents


def generate_recommendations(
    analysis: ProblemAnalysis,
    user_lat: float = 12.9716,
    user_lon: float = 77.5946,
    user_clarification: Optional[str] = None,
    property_size: Optional[str] = None,
) -> Dict[str, Any]:
    """Return only providers stored in SQLite for the requested service category."""
    database_records = list_provider_documents(analysis.category) or []
    providers: List[Dict[str, Any]] = []

    for record in database_records:
        provider = dict(record)
        provider["name"] = provider["shop_name"]
        provider["category"] = provider["service_category"]
        latitude = provider.get("latitude")
        longitude = provider.get("longitude")
        provider["distance_km"] = (
            haversine_distance_km(user_lat, user_lon, latitude, longitude)
            if latitude is not None and longitude is not None
            else None
        )
        visit_charge = provider.get("base_visit_charge")
        service_charge = provider.get("estimated_service_charge")
        if visit_charge is not None and service_charge is not None:
            provider["estimated_total"] = (
                visit_charge + service_charge + round(service_charge * 0.18)
            )
        if provider["distance_km"] is None or provider["distance_km"] <= 25:
            providers.append(provider)

    providers.sort(
        key=lambda provider: (
            provider["distance_km"] is None,
            provider["distance_km"] if provider["distance_km"] is not None else float("inf"),
            provider["shop_name"].casefold(),
        )
    )

    primary_service = None
    if providers:
        category = providers[0]["service_category"]
        primary_service = {
            "category": category,
            "name": category.replace("_", " ").title(),
            "provider_count": len(providers),
        }

    if not providers:
        notice = f"No {analysis.category.replace('_', ' ')} providers are listed in the SQLite database."
    elif analysis.intent == "book":
        booking_data = [
            provider
            for provider in providers
            if provider.get("base_visit_charge") is not None
            and provider.get("estimated_service_charge") is not None
            and provider.get("slots_available")
        ]
        if not booking_data:
            notice = (
                "The SQLite records do not include prices or available time slots, "
                "so a booking cannot be confirmed."
            )
        elif any(provider.get("booking_data_source") == "synthetic_test" for provider in booking_data):
            notice = (
                "Synthetic test prices and appointment slots are available for the demo only. "
                "They are not provider-confirmed, and no real booking has been placed."
            )
        else:
            notice = (
                "Prices and appointment slots are listed from provider records. "
                "This request only provides options; no booking has been placed."
            )
    else:
        notice = None

    return {
        "analysis": analysis.model_dump(),
        "primary_service": primary_service,
        "related_services": [],
        "pricing_estimate": None,
        "recommended_providers": providers,
        "is_emergency": bool(analysis.safety_warning) or "hazard" in analysis.issue_type or "emergency" in analysis.issue_type,
        "safety_advisory": analysis.safety_warning,
        "clarification_applied": user_clarification,
        "notice": notice,
        "data_source": "sqlite",
    }
