"""
Recommendation Engine for Local Service AI.
Synthesizes problem analysis from Qwen with MCP service catalog and provider discovery tools
to generate ranked, actionable local service recommendations.
"""
from typing import List, Dict, Any, Optional
from services.analyzer import ProblemAnalysis
from services.mcp_catalog import (
    mcp_search_catalog,
    mcp_find_providers,
    mcp_get_pricing_estimate,
)


def generate_recommendations(
    analysis: ProblemAnalysis,
    user_lat: float = 12.9716,
    user_lon: float = 77.5946,
    user_clarification: Optional[str] = None,
    property_size: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ranks suitable catalogue services and providers using MCP tools.
    """
    is_emergency = bool(analysis.safety_warning) or "hazard" in analysis.issue_type or "emergency" in analysis.issue_type

    # 1. Search MCP Catalogue
    catalog_results = mcp_search_catalog(
        category=analysis.category,
        issue_type=analysis.issue_type,
        query=analysis.problem_summary,
    )
    primary_service = catalog_results[0] if catalog_results else {
        "id": "srv_general",
        "category": analysis.category,
        "name": f"{analysis.category.replace('_', ' ').title()} General Inspection",
        "description": "Comprehensive diagnostic check by a verified professional.",
        "base_price": 299,
        "price_unit": "inspection",
        "estimated_duration_mins": 45,
        "warranty_days": 30,
    }

    # 2. Extract property size if mentioned in text or clarification
    extracted_size = property_size
    combined_text = f"{analysis.problem_summary} {user_clarification or ''}".upper()
    for size in ["1BHK", "2BHK", "3BHK", "4BHK", "VILLA"]:
        if size in combined_text:
            extracted_size = size
            break

    # 3. Calculate Pricing Estimate via MCP Tool
    pricing_estimate = mcp_get_pricing_estimate(
        service_id=primary_service.get("id", "srv_general"),
        property_size=extracted_size,
    )

    # 4. Find and Rank Providers via MCP Provider Discovery
    providers = mcp_find_providers(
        category=analysis.category,
        user_lat=user_lat,
        user_lon=user_lon,
        max_radius_km=25.0,
        emergency_only=is_emergency,
    )

    # Fallback if emergency filter returned no direct providers
    if is_emergency and not providers:
        providers = mcp_find_providers(
            category=analysis.category,
            user_lat=user_lat,
            user_lon=user_lon,
            max_radius_km=30.0,
            emergency_only=False,
        )

    # 5. Composite Ranking
    ranked_providers = []
    for prov in providers:
        # Score calculation:
        # Base: rating * 15 (max ~75)
        # Distance penalty: -2 points per km
        # Verified bonus: +10
        # Emergency bonus: +20 if emergency mode and is_emergency
        score = prov.get("rating", 4.0) * 15.0
        score -= min(30.0, prov.get("distance_km", 5.0) * 2.0)
        if prov.get("verified"):
            score += 10.0
        if is_emergency and prov.get("is_emergency"):
            score += 25.0

        prov_entry = dict(prov)
        prov_entry["composite_score"] = round(score, 1)
        prov_entry["estimated_cost"] = {
            "visiting_charge": prov.get("base_visit_charge", 199),
            "estimated_service_charge": pricing_estimate.get("estimated_service_charge", primary_service.get("base_price", 299)),
            "currency": "INR (₹)",
        }
        ranked_providers.append(prov_entry)

    # Sort by composite score descending
    ranked_providers.sort(key=lambda x: x["composite_score"], reverse=True)

    return {
        "analysis": analysis.model_dump(),
        "primary_service": primary_service,
        "related_services": catalog_results[1:3] if len(catalog_results) > 1 else [],
        "pricing_estimate": pricing_estimate,
        "recommended_providers": ranked_providers[:4],
        "is_emergency": is_emergency,
        "safety_advisory": analysis.safety_warning if is_emergency else None,
        "clarification_applied": user_clarification,
    }
