"""Canonical analytics service boundary."""

from services.analytics_service import (
    enrich_price_analysis,
    feature_importance,
    get_price_summary,
)

__all__ = ["enrich_price_analysis", "feature_importance", "get_price_summary"]
