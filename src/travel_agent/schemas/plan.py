"""Travel plan model — the final itinerary output.

The Planner Agent consumes the AnalysisResult and produces a structured,
day-by-day travel plan with time slots, budgets, and alternatives.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from travel_agent.schemas.common import (
    GeoLocation,
    MealType,
    POICategory,
    Route,
    TimeSlot,
)


class Activity(BaseModel):
    """A single activity within a day's schedule."""

    name: str = Field(..., description="Activity name")
    description: str = Field(default="", description="Brief description")
    location: Optional[GeoLocation] = Field(default=None, description="Activity location")
    category: POICategory = Field(default=POICategory.OTHER, description="Activity category")
    time_slot: TimeSlot = Field(..., description="Time slot for this activity")
    estimated_cost: Optional[float] = Field(default=None, ge=0, description="Estimated cost")
    notes: list[str] = Field(default_factory=list, description="Tips and reminders")
    tags: list[str] = Field(default_factory=list, description="Tags, e.g. '免费', '需预约'")
    poi_id: str = Field(default="", description="Reference to original POI ID")

    @property
    def display_line(self) -> str:
        time_str = f"⏰ {self.time_slot.display}"
        cost_str = f"  ¥{self.estimated_cost:.0f}" if self.estimated_cost else ""
        return f"{time_str} | {self.name}{cost_str}"

    @property
    def emoji_category(self) -> str:
        return self.category.emoji


class MealPlan(BaseModel):
    """Planned meal within the itinerary."""

    meal_type: MealType = Field(..., description="Breakfast / lunch / dinner / snack")
    suggestion: str = Field(default="", description="Recommended restaurant or food")
    location: Optional[GeoLocation] = Field(default=None, description="Restaurant location")
    estimated_cost: Optional[float] = Field(default=None, ge=0, description="Per-person cost")
    cuisine_type: str = Field(default="", description="Cuisine type")
    poi_id: str = Field(default="", description="Reference to original POI ID")
    notes: list[str] = Field(default_factory=list, description="Dining tips")

    @property
    def display(self) -> str:
        time_icons = {
            MealType.BREAKFAST: "🌅 早餐",
            MealType.LUNCH: "☀️ 午餐",
            MealType.DINNER: "🌆 晚餐",
            MealType.SNACK: "🍡 小吃",
        }
        icon = time_icons.get(self.meal_type, self.meal_type.label_cn)
        cost = f" ¥{self.estimated_cost:.0f}" if self.estimated_cost else ""
        return f"{icon}: {self.suggestion}{cost}"


class DayPlan(BaseModel):
    """Complete plan for a single day."""

    day_index: int = Field(..., ge=0, description="Day number (0-indexed)")
    title: str = Field(default="", description="Day title, e.g. '第一天: 古城探访'")
    date: Optional[str] = Field(default=None, description="Calendar date string")

    # ── Schedule ──
    activities: list[Activity] = Field(
        default_factory=list,
        description="Activities in chronological order",
    )
    meals: list[MealPlan] = Field(
        default_factory=list,
        description="Meal plan for the day",
    )

    # ── Transportation ──
    transport_between_activities: list[Route] = Field(
        default_factory=list,
        description="Transport between consecutive activities",
    )

    # ── Budget ──
    daily_budget_estimate: Optional[float] = Field(
        default=None, ge=0,
        description="Estimated total cost for the day",
    )

    # ── Lodging ──
    accommodation: Optional[str] = Field(
        default=None,
        description="Recommended accommodation for the night",
    )
    accommodation_cost: Optional[float] = Field(
        default=None, ge=0,
        description="Accommodation cost estimate",
    )

    # ── Notes ──
    tips: list[str] = Field(
        default_factory=list,
        description="Daily tips, e.g. '记得带伞', '穿舒适的鞋子'",
    )
    weather_note: str = Field(
        default="",
        description="Weather reminder for this day",
    )

    # ── Display helpers ──

    @property
    def display_header(self) -> str:
        date_str = f" ({self.date})" if self.date else ""
        return f"📅 {self.title}{date_str}"

    @property
    def timeline(self) -> list[str]:
        """Return chronological display lines for Streamlit."""
        lines: list[str] = []
        for activity in self.activities:
            lines.append(activity.display_line)
        return lines

    @property
    def total_estimated_cost(self) -> float:
        cost = 0.0
        for a in self.activities:
            if a.estimated_cost:
                cost += a.estimated_cost
        for m in self.meals:
            if m.estimated_cost:
                cost += m.estimated_cost
        if self.accommodation_cost:
            cost += self.accommodation_cost
        return cost


class BudgetBreakdown(BaseModel):
    """Detailed budget breakdown for the entire trip."""

    total_estimated: float = Field(default=0, ge=0, description="Total estimated cost")
    accommodation_total: float = Field(default=0, ge=0, description="Total accommodation cost")
    food_total: float = Field(default=0, ge=0, description="Total food cost")
    transportation_total: float = Field(default=0, ge=0, description="Total transportation cost")
    activities_total: float = Field(default=0, ge=0, description="Total activities/tickets cost")
    miscellaneous_total: float = Field(default=0, ge=0, description="Miscellaneous costs")
    currency: str = Field(default="CNY", description="Currency code")

    @property
    def breakdown_items(self) -> dict[str, float]:
        return {
            "🏨 住宿": self.accommodation_total,
            "🍽️ 餐饮": self.food_total,
            "🚗 交通": self.transportation_total,
            "🎫 活动": self.activities_total,
            "📦 其他": self.miscellaneous_total,
        }

    @property
    def display(self) -> str:
        return f"总预算: ¥{self.total_estimated:,.0f}"


class TravelPlan(BaseModel):
    """Complete travel itinerary — the final output of the Planner Agent.

    This is the culmination of the entire multi-agent pipeline,
    presented to the user via Streamlit.
    """

    # ── Plan identity ──
    title: str = Field(default="我的旅行计划", description="Plan title")
    destination: str = Field(default="", description="Destination summary")

    # ── Daily plans ──
    days: list[DayPlan] = Field(
        default_factory=list,
        description="Day-by-day itinerary",
    )

    # ── Budget ──
    budget_breakdown: BudgetBreakdown = Field(
        default_factory=BudgetBreakdown,
        description="Detailed budget breakdown",
    )

    # ── Alternatives ──
    alternatives: list[str] = Field(
        default_factory=list,
        description="Alternative suggestions (text descriptions)",
    )
    flexible_options: list[DayPlan] = Field(
        default_factory=list,
        description="Alternative day plans for flexibility",
    )

    # ── Summary ──
    overview: str = Field(
        default="",
        description="One-paragraph trip overview for the user",
    )

    # ── Practical info ──
    notes: list[str] = Field(
        default_factory=list,
        description="General travel tips for the trip",
    )
    packing_tips: list[str] = Field(
        default_factory=list,
        description="What to pack based on weather and activities",
    )
    emergency_info: str = Field(
        default="",
        description="Emergency contacts and useful numbers",
    )

    # ── Display helpers ──

    @property
    def display_summary(self) -> str:
        return f"📍 {self.destination} | 📅 {len(self.days)}天行程 | 💰 ¥{self.budget_breakdown.total_estimated:,.0f}"

    def get_day(self, index: int) -> Optional[DayPlan]:
        """Get the plan for a specific day."""
        if 0 <= index < len(self.days):
            return self.days[index]
        return None

    @property
    def total_days(self) -> int:
        return len(self.days)

    @property
    def total_estimated_cost(self) -> float:
        return self.budget_breakdown.total_estimated
