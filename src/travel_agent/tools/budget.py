"""Mock budget estimation tool — returns a detailed budget breakdown.

MVP uses mock data. Structure matches travel_agent.schemas.plan.BudgetBreakdown.
Replace with real price API / database lookups in Phase 2.
"""

from travel_agent.schemas.common import BudgetLevel, POICategory
from travel_agent.schemas.plan import BudgetBreakdown
from travel_agent.schemas.travel import TravelPreferences


def estimate_budget(
    days: int,
    preferences: TravelPreferences,
    companions: int = 1,
) -> BudgetBreakdown:
    """Estimate a trip budget based on duration and preferences.

    Args:
        days: Number of travel days.
        preferences: User's travel style and interests.
        companions: Number of travelers.

    Returns:
        BudgetBreakdown with estimated costs per category.
    """
    # Per-day base costs by budget level
    level = preferences.accommodation_type if hasattr(preferences, 'accommodation_type') else "hotel"
    level_multipliers = {
        "economy": {"hotel": 200, "food": 80, "transport": 30, "activity": 50, "misc": 20},
        "hostel": {"hotel": 150, "food": 60, "transport": 25, "activity": 40, "misc": 15},
        "民宿": {"hotel": 300, "food": 100, "transport": 40, "activity": 60, "misc": 30},
        "hotel": {"hotel": 400, "food": 120, "transport": 50, "activity": 80, "misc": 40},
        "comfort": {"hotel": 400, "food": 120, "transport": 50, "activity": 80, "misc": 40},
        "舒适型": {"hotel": 400, "food": 120, "transport": 50, "activity": 80, "misc": 40},
        "luxury": {"hotel": 800, "food": 200, "transport": 80, "activity": 150, "misc": 60},
        "豪华型": {"hotel": 800, "food": 200, "transport": 80, "activity": 150, "misc": 60},
    }

    mult = level_multipliers.get(level) or level_multipliers["hotel"]

    # Factor in interests
    interest_factors = {
        POICategory.ATTRACTION: 1.2,
        POICategory.RESTAURANT: 1.3,
        POICategory.ENTERTAINMENT: 1.4,
        POICategory.SHOPPING: 1.5,
        POICategory.MUSEUM: 0.8,
        POICategory.PARK: 0.7,
    }

    # Average activity factor
    activity_factor = 1.0
    if preferences.interests:
        factors = [interest_factors.get(c, 1.0) for c in preferences.interests]
        activity_factor = sum(factors) / len(factors)

    daily_activity = mult["activity"] * activity_factor
    daily_food = mult["food"]
    daily_hotel = mult["hotel"]
    daily_transport = mult["transport"]
    daily_misc = mult["misc"]

    return BudgetBreakdown(
        accommodation_total=round(daily_hotel * days * companions * 0.7),
        food_total=round(daily_food * days * companions),
        transportation_total=round(daily_transport * days * companions + 200),
        activities_total=round(daily_activity * days * companions),
        miscellaneous_total=round(daily_misc * days * companions),
        total_estimated=round(
            daily_hotel * days * companions * 0.7
            + daily_food * days * companions
            + daily_transport * days * companions + 200
            + daily_activity * days * companions
            + daily_misc * days * companions
        ),
        currency="CNY",
    )
