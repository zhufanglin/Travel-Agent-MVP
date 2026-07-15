"""Travel intent model — structured representation of user's travel request.

This is the first structured data produced by the Coordinator Agent
after parsing the user's natural language input. It drives the entire
workflow: all downstream agents use it as the source of truth for
what the user wants.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from travel_agent.schemas.common import Budget, BudgetLevel, POICategory


class TravelPreferences(BaseModel):
    """User's travel style and interests."""

    interests: list[POICategory] = Field(
        default_factory=list,
        description="POI categories the user is interested in",
    )
    cuisine_preferences: list[str] = Field(
        default_factory=list,
        description="Preferred cuisine types, e.g. ['川菜', '粤菜', '日料']",
    )
    pace: str = Field(
        default="moderate",
        description="Travel pace: 'relaxed', 'moderate', 'intensive'",
    )
    accommodation_type: str = Field(
        default="hotel",
        description="Preferred accommodation type",
    )
    special_requirements: list[str] = Field(
        default_factory=list,
        description="Special requirements, e.g. ['无障碍', '亲子友好', '拍照打卡']",
    )

    @property
    def pace_label_cn(self) -> str:
        labels = {"relaxed": "轻松", "moderate": "适中", "intensive": "紧凑"}
        return labels.get(self.pace, self.pace)

    @property
    def interest_labels(self) -> list[str]:
        return [c.label_cn for c in self.interests]


class TravelConstraints(BaseModel):
    """Hard constraints the user has specified."""

    max_budget: Optional[Budget] = Field(default=None, description="Maximum total budget")
    budget_level: Optional[BudgetLevel] = Field(default=None, description="Budget level preference")
    must_visit: list[str] = Field(default_factory=list, description="Must-visit places")
    avoid_places: list[str] = Field(default_factory=list, description="Places to avoid")
    transportation_mode: Optional[str] = Field(
        default=None,
        description="Preferred transportation mode",
    )
    dietary_restrictions: list[str] = Field(
        default_factory=list,
        description="Dietary restrictions, e.g. ['素食', '清真']",
    )
    mobility_concerns: bool = Field(
        default=False,
        description="Whether mobility/walking limitations exist",
    )


class TravelIntent(BaseModel):
    """Structured representation of user's travel intent.

    Parsed from natural language by the Coordinator Agent.
    Fields marked Optional may be None if not yet clarified —
    the Coordinator should ask the user before proceeding.
    """

    # ── Core fields ──
    destination: Optional[str] = Field(
        default=None,
        description="Destination city or region",
    )
    origin: Optional[str] = Field(
        default=None,
        description="Departure city (if specified)",
    )

    # ── Time ──
    start_date: Optional[date] = Field(
        default=None,
        description="Trip start date",
    )
    end_date: Optional[date] = Field(
        default=None,
        description="Trip end date (mutually exclusive with duration_days)",
    )
    duration_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Number of travel days (mutually exclusive with end_date)",
    )

    # ── People ──
    companions: int = Field(
        default=1,
        ge=1,
        le=100,
        description="Number of travelers (including self)",
    )
    companion_info: str = Field(
        default="",
        description="Companion description, e.g. '带父母', '情侣', '带5岁小孩'",
    )

    # ── Budget ──
    budget: Optional[Budget] = Field(
        default=None,
        description="Budget constraints (total trip budget)",
    )

    # ── Preferences & Constraints ──
    preferences: TravelPreferences = Field(
        default_factory=TravelPreferences,
        description="Travel style and interests",
    )
    constraints: TravelConstraints = Field(
        default_factory=TravelConstraints,
        description="Hard constraints and limitations",
    )

    # ── Purpose ──
    purpose: str = Field(
        default="leisure",
        description="Trip purpose: 'leisure', 'business', 'family', 'adventure', etc.",
    )

    # ── Metadata ──
    raw_input: str = Field(
        default="",
        description="Original user input text for reference",
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Fields that still need clarification from user",
    )

    # ── Display helpers ──

    @property
    def date_display(self) -> str:
        if self.start_date and self.end_date:
            return f"{self.start_date.isoformat()} → {self.end_date.isoformat()}"
        if self.start_date and self.duration_days:
            end = self.start_date.isoformat()
            return f"{self.start_date.isoformat()} (共{self.duration_days}天)"
        if self.duration_days:
            return f"{self.duration_days}天"
        return "未确定"

    @property
    def destination_display(self) -> str:
        return self.destination or "未指定目的地"

    @property
    def people_display(self) -> str:
        base = f"{self.companions}人"
        if self.companion_info:
            base += f"（{self.companion_info}）"
        return base

    @property
    def summary(self) -> str:
        """Compact one-line summary for Streamlit display."""
        parts = [
            f"📍 {self.destination_display}",
            self.date_display,
            self.people_display,
        ]
        if self.budget:
            parts.append(self.budget.display)
        if self.preferences.interests:
            parts.append("兴趣: " + "、".join(self.preferences.interest_labels))
        return " | ".join(parts)

    @property
    def is_complete(self) -> bool:
        """Whether core fields are sufficient to start research."""
        return all([
            self.destination is not None,
            self.start_date is not None or self.duration_days is not None,
        ])
