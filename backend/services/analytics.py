"""Canonical analytics service boundary."""

from services.analytics_service import (
    classify_fair_price,
    enrich_price_analysis,
    feature_importance,
    get_price_summary,
    get_storytelling_insights,
    simulate_facility_upgrades,
)

__all__ = [
    "classify_fair_price",
    "enrich_price_analysis",
    "feature_importance",
    "get_price_summary",
    "get_storytelling_insights",
    "simulate_facility_upgrades",
]
