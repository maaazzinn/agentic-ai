"""
MCP Service Catalogue and Provider Discovery Tools.
Provides MCP-compatible tools to retrieve verified local services, pricing estimates,
and real providers based on geographic proximity and service requirements.
"""
import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Realistic Service Catalogue
SERVICES_CATALOGUE: List[Dict[str, Any]] = [
    # Plumbing
    {
        "id": "srv_plumb_tap",
        "category": "plumbing",
        "issue_types": ["tap_repair", "faucet_repair", "leakage"],
        "name": "Tap & Faucet Repair / Replacement",
        "description": "Fixing dripping, continuous leaks, washer replacement, or full faucet cartridge swap.",
        "base_price": 249,
        "price_unit": "per fixture",
        "estimated_duration_mins": 30,
        "urgency_level": "normal",
        "warranty_days": 30,
    },
    {
        "id": "srv_plumb_drain",
        "category": "plumbing",
        "issue_types": ["drainage_block", "sink_block", "toilet_block"],
        "name": "Drainage & Clog Clearance",
        "description": "Heavy-duty mechanical snake and enzyme clearance for blocked sinks, showers, or drains.",
        "base_price": 399,
        "price_unit": "per drain",
        "estimated_duration_mins": 45,
        "urgency_level": "high",
        "warranty_days": 15,
    },
    {
        "id": "srv_plumb_pipe",
        "category": "plumbing",
        "issue_types": ["pipe_burst", "pipe_leakage", "water_leak"],
        "name": "Concealed & Exposed Pipe Leak Repair",
        "description": "Detection and sealing of leaking or cracked CPVC/PPR pipes with pressure test.",
        "base_price": 499,
        "price_unit": "per point",
        "estimated_duration_mins": 60,
        "urgency_level": "high",
        "warranty_days": 60,
    },

    # AC Repair
    {
        "id": "srv_ac_cooling",
        "category": "ac_repair",
        "issue_types": ["cooling_problem", "not_cooling", "weak_cooling", "gas_leak"],
        "name": "AC Cooling Diagnosis & Gas Refill",
        "description": "Complete diagnostic check of refrigerant pressure, compressor health, and airflow.",
        "base_price": 599,
        "price_unit": "inspection + gas as needed",
        "estimated_duration_mins": 45,
        "urgency_level": "normal",
        "warranty_days": 60,
    },
    {
        "id": "srv_ac_foam_jet",
        "category": "ac_repair",
        "issue_types": ["ac_servicing", "weak_airflow", "smell", "maintenance"],
        "name": "AC Deep Cleaning & Foam-Jet Service",
        "description": "High-pressure foam jet wash of indoor cooling coils and outdoor condenser unit.",
        "base_price": 449,
        "price_unit": "per unit",
        "estimated_duration_mins": 45,
        "urgency_level": "normal",
        "warranty_days": 30,
    },

    # Electrical
    {
        "id": "srv_elec_emergency",
        "category": "electrical",
        "issue_types": ["socket_hazard", "switch_hazard", "sparking", "short_circuit", "burning_smell"],
        "name": "Emergency Electrical Hazard & Socket Repair",
        "description": "Urgent on-site inspection for burnt sockets, sparking switches, or short circuits with circuit testing.",
        "base_price": 299,
        "price_unit": "emergency diagnostic fee",
        "estimated_duration_mins": 30,
        "urgency_level": "emergency",
        "warranty_days": 90,
    },
    {
        "id": "srv_elec_breaker",
        "category": "electrical",
        "issue_types": ["mcb_trip", "breaker_replacement", "wiring_fault"],
        "name": "MCB / Circuit Breaker & Panel Repair",
        "description": "Diagnosing recurring breaker trips, panel overheating, and rewiring faulty circuits.",
        "base_price": 349,
        "price_unit": "per breaker/circuit",
        "estimated_duration_mins": 45,
        "urgency_level": "high",
        "warranty_days": 90,
    },

    # Appliance Repair
    {
        "id": "srv_app_washing_drum",
        "category": "appliance_repair",
        "issue_types": ["washing_machine_noise", "drum_vibration", "bearing_noise", "spin_issue"],
        "name": "Washing Machine Drum & Motor Noise Repair",
        "description": "Diagnosis of abnormal spinning noise, worn drum bearings, shock absorber failure, or belt replacement.",
        "base_price": 399,
        "price_unit": "visiting & inspection",
        "estimated_duration_mins": 60,
        "urgency_level": "normal",
        "warranty_days": 60,
    },
    {
        "id": "srv_app_fridge",
        "category": "appliance_repair",
        "issue_types": ["refrigerator_not_cooling", "fridge_noise", "freezer_frost"],
        "name": "Refrigerator Cooling & Thermostat Repair",
        "description": "Compressor relay testing, defrost timer/heater check, and gas charging.",
        "base_price": 399,
        "price_unit": "visiting & inspection",
        "estimated_duration_mins": 45,
        "urgency_level": "normal",
        "warranty_days": 60,
    },

    # Home Cleaning
    {
        "id": "srv_clean_deep_2bhk",
        "category": "home_cleaning",
        "issue_types": ["deep_cleaning", "2bhk_cleaning", "apartment_cleaning", "move_in_cleaning"],
        "name": "Full Home Deep Cleaning (2BHK)",
        "description": "Machine scrub of floors, kitchen degreasing, bathroom descaling, balcony wash, and cobweb removal.",
        "base_price": 2999,
        "price_unit": "per 2BHK apartment",
        "estimated_duration_mins": 240,
        "urgency_level": "normal",
        "warranty_days": 7,
    },
    {
        "id": "srv_clean_bath_kitchen",
        "category": "home_cleaning",
        "issue_types": ["bathroom_cleaning", "kitchen_cleaning"],
        "name": "Intense Kitchen & Bathroom Sanitization",
        "description": "Tile grout descaling, oil exhaust cleaning, sanitaryware polishing, and steam sanitization.",
        "base_price": 1299,
        "price_unit": "combo",
        "estimated_duration_mins": 120,
        "urgency_level": "normal",
        "warranty_days": 7,
    },

    # Car Wash
    {
        "id": "srv_car_doorstep",
        "category": "car_wash",
        "issue_types": ["car_wash", "car_cleaning", "interior_detailing"],
        "name": "Doorstep Foam Wash & Interior Vacuuming",
        "description": "High pressure wash, foam cannon body cleaning, tire shine, and deep interior dust extraction.",
        "base_price": 549,
        "price_unit": "per vehicle",
        "estimated_duration_mins": 60,
        "urgency_level": "normal",
        "warranty_days": 3,
    },
]

# Verified Local Service Providers Database
SERVICE_PROVIDERS: List[Dict[str, Any]] = [
    # Plumbing Providers
    {
        "id": "prov_plumb_1",
        "name": "AquaShield Master Plumbers",
        "category": "plumbing",
        "rating": 4.9,
        "reviews_count": 342,
        "verified": True,
        "badge": "Top Rated Pro",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "phone": "+91 98450 11223",
        "base_visit_charge": 199,
        "eta_minutes": 25,
        "is_emergency": False,
        "slots_available": ["Today 11:30 AM", "Today 02:00 PM", "Tomorrow 10:00 AM"],
    },
    {
        "id": "prov_plumb_2",
        "name": "Express Rapid Plumbing",
        "category": "plumbing",
        "rating": 4.7,
        "reviews_count": 189,
        "verified": True,
        "badge": "Fast Responder",
        "latitude": 12.9820,
        "longitude": 77.6050,
        "phone": "+91 98450 22334",
        "base_visit_charge": 249,
        "eta_minutes": 15,
        "is_emergency": True,
        "slots_available": ["Within 30 mins", "Today 03:00 PM"],
    },

    # AC Repair Providers
    {
        "id": "prov_ac_1",
        "name": "CoolBreeze Climate Experts",
        "category": "ac_repair",
        "rating": 4.8,
        "reviews_count": 512,
        "verified": True,
        "badge": "Certified Inverter Tech",
        "latitude": 12.9650,
        "longitude": 77.5850,
        "phone": "+91 98450 33445",
        "base_visit_charge": 299,
        "eta_minutes": 35,
        "is_emergency": False,
        "slots_available": ["Today 12:00 PM", "Today 04:30 PM", "Tomorrow 11:00 AM"],
    },
    {
        "id": "prov_ac_2",
        "name": "FrostLine AC Services & Spares",
        "category": "ac_repair",
        "rating": 4.6,
        "reviews_count": 274,
        "verified": True,
        "badge": "Authorized Spares",
        "latitude": 12.9550,
        "longitude": 77.6200,
        "phone": "+91 98450 44556",
        "base_visit_charge": 249,
        "eta_minutes": 45,
        "is_emergency": False,
        "slots_available": ["Today 02:00 PM", "Tomorrow 09:30 AM"],
    },

    # Electrical Providers
    {
        "id": "prov_elec_1",
        "name": "SparkSafe Emergency Electricians",
        "category": "electrical",
        "rating": 4.9,
        "reviews_count": 680,
        "verified": True,
        "badge": "Licensed Master Electrician",
        "latitude": 12.9750,
        "longitude": 77.5990,
        "phone": "+91 98450 55667",
        "base_visit_charge": 299,
        "eta_minutes": 15,
        "is_emergency": True,
        "slots_available": ["Immediate Emergency Dispatch (15-20 min)", "Today 01:00 PM"],
    },
    {
        "id": "prov_elec_2",
        "name": "Voltz Home Electrical Solutions",
        "category": "electrical",
        "rating": 4.7,
        "reviews_count": 215,
        "verified": True,
        "badge": "Safety Certified",
        "latitude": 12.9900,
        "longitude": 77.5800,
        "phone": "+91 98450 66778",
        "base_visit_charge": 249,
        "eta_minutes": 30,
        "is_emergency": True,
        "slots_available": ["Immediate Dispatch (30 min)", "Today 03:00 PM"],
    },

    # Appliance Repair Providers
    {
        "id": "prov_app_1",
        "name": "DrumCare Appliance Engineers",
        "category": "appliance_repair",
        "rating": 4.8,
        "reviews_count": 420,
        "verified": True,
        "badge": "Washer & Dryer Specialist",
        "latitude": 12.9600,
        "longitude": 77.6100,
        "phone": "+91 98450 77889",
        "base_visit_charge": 299,
        "eta_minutes": 40,
        "is_emergency": False,
        "slots_available": ["Today 01:30 PM", "Today 05:00 PM", "Tomorrow 11:30 AM"],
    },
    {
        "id": "prov_app_2",
        "name": "FixCraft Multi-Brand Appliance Care",
        "category": "appliance_repair",
        "rating": 4.6,
        "reviews_count": 195,
        "verified": True,
        "badge": "Genuine Parts Assured",
        "latitude": 12.9400,
        "longitude": 77.5700,
        "phone": "+91 98450 88990",
        "base_visit_charge": 249,
        "eta_minutes": 50,
        "is_emergency": False,
        "slots_available": ["Today 03:30 PM", "Tomorrow 10:00 AM"],
    },

    # Home Cleaning Providers
    {
        "id": "prov_clean_1",
        "name": "Pristine Spaces Deep Cleaning Co.",
        "category": "home_cleaning",
        "rating": 4.9,
        "reviews_count": 890,
        "verified": True,
        "badge": "Eco-Friendly Pro Team",
        "latitude": 12.9780,
        "longitude": 77.6250,
        "phone": "+91 98450 99001",
        "base_visit_charge": 499,
        "eta_minutes": 60,
        "is_emergency": False,
        "slots_available": ["Today 02:00 PM", "This Friday 09:00 AM", "Saturday 08:30 AM", "Saturday 01:30 PM"],
    },
    {
        "id": "prov_clean_2",
        "name": "UrbanGlow Home Sanitization",
        "category": "home_cleaning",
        "rating": 4.7,
        "reviews_count": 310,
        "verified": True,
        "badge": "Industrial Grade Equipment",
        "latitude": 12.9500,
        "longitude": 77.6350,
        "phone": "+91 98450 00112",
        "base_visit_charge": 399,
        "eta_minutes": 75,
        "is_emergency": False,
        "slots_available": ["Today 02:00 PM", "Tomorrow 09:00 AM", "Friday 02:00 PM", "Saturday 10:00 AM"],
    },

    # Car Wash Providers
    {
        "id": "prov_car_1",
        "name": "SpeedyShine Doorstep Car Wash",
        "category": "car_wash",
        "rating": 4.8,
        "reviews_count": 360,
        "verified": True,
        "badge": "Waterless & Foam Specialist",
        "latitude": 12.9700,
        "longitude": 77.6100,
        "phone": "+91 98450 12345",
        "base_visit_charge": 199,
        "eta_minutes": 30,
        "is_emergency": False,
        "slots_available": ["Today 11:00 AM", "Today 02:30 PM", "Tomorrow 08:30 AM"],
    },
]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(r * c, 2)


# ==========================================
# MCP TOOLS IMPLEMENTATION
# ==========================================

def mcp_search_catalog(category: str, issue_type: Optional[str] = None, query: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    MCP Tool: Searches the service catalogue matching category, issue type, or keywords.
    """
    cat_lower = (category or "").lower()
    issue_lower = (issue_type or "").lower()
    query_lower = (query or "").lower()

    results = []
    for item in SERVICES_CATALOGUE:
        item_cat = item["category"].lower()
        if cat_lower and item_cat != cat_lower and cat_lower != "other":
            continue

        match_score = 0
        if cat_lower == item_cat:
            match_score += 10
        if issue_lower and any(issue_lower in t or t in issue_lower for t in item["issue_types"]):
            match_score += 20
        if query_lower:
            if query_lower in item["name"].lower():
                match_score += 15
            if query_lower in item["description"].lower():
                match_score += 10

        item_copy = dict(item)
        item_copy["relevance_score"] = match_score
        results.append(item_copy)

    # Sort descending by relevance
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results


def mcp_find_providers(
    category: str,
    user_lat: float = 12.9716,
    user_lon: float = 77.5946,
    max_radius_km: float = 25.0,
    emergency_only: bool = False,
) -> List[Dict[str, Any]]:
    """
    MCP Tool: Finds nearby verified service providers, computing actual distance and estimated arrival time.
    """
    cat_lower = (category or "").lower()
    matched = []

    for prov in SERVICE_PROVIDERS:
        prov_cat = prov["category"].lower()
        if cat_lower and prov_cat != cat_lower and cat_lower != "other":
            continue
        if emergency_only and not prov.get("is_emergency"):
            continue

        dist = haversine_distance_km(user_lat, user_lon, prov["latitude"], prov["longitude"])
        if dist <= max_radius_km:
            prov_copy = dict(prov)
            prov_copy["distance_km"] = dist
            # Dynamic ETA based on distance (assumes 25 km/h urban speed + 10 min prep)
            estimated_transit = int(dist * 2.4) + 10
            prov_copy["eta_minutes"] = max(prov.get("eta_minutes", 20), estimated_transit)
            matched.append(prov_copy)

    # If no provider within radius, return category providers sorted by distance
    if not matched:
        for prov in SERVICE_PROVIDERS:
            if prov["category"].lower() == cat_lower:
                dist = haversine_distance_km(user_lat, user_lon, prov["latitude"], prov["longitude"])
                p_copy = dict(prov)
                p_copy["distance_km"] = dist
                matched.append(p_copy)

    # Rank by rating (descending) and distance (ascending)
    matched.sort(key=lambda p: (-p["rating"], p["distance_km"]))
    return matched


def mcp_get_pricing_estimate(service_id: str, property_size: Optional[str] = None) -> Dict[str, Any]:
    """
    MCP Tool: Returns itemized pricing estimate for a selected service.
    """
    service = next((s for s in SERVICES_CATALOGUE if s["id"] == service_id), None)
    if not service:
        return {"error": f"Service ID {service_id} not found", "estimated_total": 350}

    base = service["base_price"]
    multiplier = 1.0
    if property_size:
        size = property_size.upper()
        if "1BHK" in size:
            multiplier = 0.8
        elif "2BHK" in size:
            multiplier = 1.0
        elif "3BHK" in size:
            multiplier = 1.4
        elif "VILLA" in size or "4BHK" in size:
            multiplier = 2.0

    estimated_total = round(base * multiplier)
    tax = round(estimated_total * 0.18)
    return {
        "service_name": service["name"],
        "base_price": base,
        "property_size_multiplier": multiplier,
        "estimated_service_charge": estimated_total,
        "gst_tax": tax,
        "estimated_total": estimated_total + tax,
        "warranty_days": service["warranty_days"],
    }
