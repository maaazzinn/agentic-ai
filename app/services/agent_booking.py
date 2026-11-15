"""
Agentic Booking Engine — prepares local demo bookings.
When intent == "book", the agent:
  1. Searches MCP catalogue for the right service
  2. Finds providers filtered by time + sorted by booking_priority
  3. Auto-selects the best match
  4. Returns a demo confirmation without contacting an external provider
"""
import time
import re
from typing import Dict, Any, Optional, List
from .mcp_catalog import (
    mcp_search_catalog,
    mcp_find_providers,
    mcp_get_pricing_estimate,
)
from .analyzer import ProblemAnalysis


def _slot_matches_preference(slot: str, preference: str) -> bool:
    requested = preference.lower().strip()
    requested_time = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", requested)
    if requested_time:
        slot_time = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", slot.lower())
        if not slot_time or (
            int(slot_time.group(1)) != int(requested_time.group(1))
            or (slot_time.group(2) or "00") != (requested_time.group(2) or "00")
            or slot_time.group(3) != requested_time.group(3)
        ):
            return False

    day_terms = re.findall(
        r"\b(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        requested,
    )
    if day_terms and not all(day in slot.lower() for day in day_terms):
        return False

    if not requested_time and not day_terms:
        return requested in slot.lower()

    period = re.search(r"\b(morning|afternoon|evening)\b", requested)
    if period:
        slot_time = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", slot.lower())
        if not slot_time:
            return False
        hour = int(slot_time.group(1)) % 12 + (12 if slot_time.group(3) == "pm" else 0)
        if period.group(1) == "morning" and hour >= 12:
            return False
        if period.group(1) == "afternoon" and not 12 <= hour < 17:
            return False
        if period.group(1) == "evening" and hour < 17:
            return False

    return bool(requested_time or day_terms)


def execute_agent_booking(
    analysis: ProblemAnalysis,
    user_lat: float = 12.9716,
    user_lon: float = 77.5946,
) -> Dict[str, Any]:
    """
    Autonomous agent that picks the best provider and 'books' it
    based on user's stated priority: cheapest | fastest | top_rated.
    """
    steps: List[str] = []

    # Step 1 — Find matching services
    steps.append(f"🔍 Searching catalogue for '{analysis.category}' — issue: {analysis.issue_type}")
    catalog = mcp_search_catalog(category=analysis.category, issue_type=analysis.issue_type)
    primary_service = catalog[0] if catalog else {
        "id": "srv_general",
        "name": f"{analysis.category.replace('_', ' ').title()} Service",
        "base_price": 299,
        "price_unit": "inspection",
        "estimated_duration_mins": 45,
        "warranty_days": 30,
        "description": "Professional on-site diagnosis and service.",
    }
    steps.append(f"✅ Matched service: **{primary_service['name']}** (base ₹{primary_service['base_price']})")

    # Step 2 — Find providers
    is_emergency = analysis.intent == "urgent" or "hazard" in analysis.issue_type
    steps.append(f"📍 Locating verified providers within 25 km...")
    providers = mcp_find_providers(
        category=analysis.category,
        user_lat=user_lat,
        user_lon=user_lon,
        max_radius_km=25.0,
        emergency_only=is_emergency,
    )
    if not providers:
        providers = mcp_find_providers(
            category=analysis.category,
            user_lat=user_lat,
            user_lon=user_lon,
            max_radius_km=40.0,
            emergency_only=False,
        )

    steps.append(f"✅ Found {len(providers)} verified providers")
    if not providers:
        return {
            "agent_mode": True,
            "success": False,
            "steps": steps,
            "message": "No providers are available for this category right now.",
        }

    # Step 3 — Keep only providers that actually have the requested slot.
    time_pref = (analysis.time_preference or "").lower()
    available_matches = []
    if time_pref:
        steps.append(f"🕐 Filtering for time preference: '{analysis.time_preference}'")
        for prov in providers:
            for slot in prov.get("slots_available", []):
                if _slot_matches_preference(slot, time_pref):
                    available_matches.append((prov, slot))

        if not available_matches:
            available_slots = [
                f"{provider['name']}: {slot}"
                for provider in providers
                for slot in provider.get("slots_available", [])
            ]
            return {
                "agent_mode": True,
                "success": False,
                "steps": steps,
                "message": (
                    f"No provider has an available slot matching '{analysis.time_preference}'. "
                    "Please choose from the available times: " + "; ".join(available_slots)
                ),
                "available_slots": available_slots,
            }
        providers = [provider for provider, _ in available_matches]

    # Step 4 — Sort by booking_priority
    priority = analysis.booking_priority
    steps.append(f"⚖️ Ranking by priority: **{priority}**")

    property_match = re.search(r"\b(?:1|2|3|4)\s*bhk\b|\bvilla\b", analysis.problem_summary, re.I)
    property_size = property_match.group(0).replace(" ", "").upper() if property_match else None
    pricing_by_service = mcp_get_pricing_estimate(primary_service.get("id", ""), property_size)

    if priority == "cheapest":
        providers.sort(
            key=lambda p: p.get("base_visit_charge", 999)
            + pricing_by_service.get("estimated_service_charge", primary_service.get("base_price", 299))
            + pricing_by_service.get("gst_tax", 0)
        )
        steps.append("💰 Sorted providers: lowest estimated total price first")
    elif priority == "fastest":
        providers.sort(key=lambda p: p.get("eta_minutes", 999))
        steps.append("⚡ Sorted providers: shortest ETA first")
    else:  # top_rated
        providers.sort(key=lambda p: (-p.get("rating", 0), p.get("distance_km", 99)))
        steps.append("⭐ Sorted providers: highest rating first")

    # Step 5 — Auto-select best provider
    if not providers:
        return {
            "agent_mode": True,
            "success": False,
            "steps": steps,
            "message": "No providers available for this category. Please try again later.",
        }

    selected = providers[0]
    selected_slot = next(
        (slot for provider, slot in available_matches if provider["id"] == selected["id"]),
        selected["slots_available"][0] if selected.get("slots_available") else "Next available",
    )

    steps.append(f"✅ Selected: **{selected['name']}** — {priority} option")
    steps.append(f"📅 Selected slot: **{selected_slot}**")

    # Step 6 — Pricing estimate
    pricing = pricing_by_service
    total = (
        selected["base_visit_charge"]
        + pricing.get("estimated_service_charge", primary_service.get("base_price", 299))
        + pricing.get("gst_tax", 0)
    )

    # Build confirmation
    booking_ref = f"LSA-{int(time.time()) % 100000}"
    steps.append(f"✅ Demo booking prepared. Reference: **{booking_ref}**")

    return {
        "agent_mode": True,
        "success": True,
        "booking_status": "demo_confirmed",
        "booking_ref": booking_ref,
        "intent": analysis.intent,
        "category": analysis.category,
        "priority_applied": priority,
        "time_preference": analysis.time_preference,
        "steps": steps,
        "selected_provider": selected,
        "selected_slot": selected_slot,
        "service": primary_service,
        "pricing": {
            "visit_charge": selected["base_visit_charge"],
            "estimated_service_charge": pricing.get("estimated_service_charge", primary_service.get("base_price", 299)),
            "gst": pricing.get("gst_tax", 0),
            "estimated_total": total,
            "currency": "INR (₹)",
        },
        "all_providers_considered": len(providers),
        "agent_message": (
            f"I prepared a demo booking with **{selected['name']}** for your **{primary_service['name']}** "
            f"at **{selected_slot}** — {priority} option available. "
            f"Estimated total: ₹{total}, including the visit charge and GST. "
            "No external provider has been contacted."
        ),
    }
