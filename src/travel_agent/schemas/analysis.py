"""Analysis result model — filtered, scored, and clustered recommendations.

The Analyst Agent takes raw ResearchReport data and applies the user's
preferences/constraints to produce actionable recommendations.
All reasoning must cite specific fields from the ResearchReport.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from travel_agent.schemas.common import POI


class ScoredPOI(BaseModel):
    """A POI with analysis score and recommendation rationale."""

    poi: POI = Field(..., description="The point of interest")
    score: float = Field(
        ..., ge=0, le=10,
        description="Recommendation score (0-10, higher = more recommended)",
    )
    match_reasons: list[str] = Field(
        default_factory=list,
        description="Why this POI matches user preferences",
        # Examples: ["评分高 (4.8)", "符合川菜偏好", "距离景点近"]
    )
    concerns: list[str] = Field(
        default_factory=list,
        description="Potential concerns to mention to user",
    )
    suggested_visit_duration: Optional[str] = Field(
        default=None,
        description="Suggested time to spend here, e.g. '2-3小时'",
    )
    recommended_meal: Optional[str] = Field(
        default=None,
        description="Best meal time if this is a restaurant",
    )

    @property
    def score_stars(self) -> str:
        """Display score as star rating for Streamlit."""
        full = round(self.score / 2)
        return "⭐" * full + "☆" * (5 - full)

    @property
    def summary(self) -> str:
        return f"{self.poi.display_name} | 评分 {self.score:.1f}/10"


class DailyCluster(BaseModel):
    """A cluster of POIs grouped for a single day."""

    day_index: int = Field(..., ge=0, description="Day number (0-indexed)")
    label: str = Field(default="", description="Theme label, e.g. '第一天: 老城区文化之旅'")
    pois: list[ScoredPOI] = Field(
        default_factory=list,
        description="Recommended POIs for this day",
    )
    area: str = Field(default="", description="Suggested area/district focus")
    estimated_budget: Optional[float] = Field(
        default=None, ge=0,
        description="Estimated cost for this day",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="General notes for this day's planning",
    )


class AnalysisResult(BaseModel):
    """Complete analysis output from the Analyst Agent.

    This bridges raw research data and final itinerary planning.
    The Planner Agent consumes this to build the day-by-day schedule.
    """

    # ── Summary ──
    summary: str = Field(
        default="",
        description="Overall analysis summary for the user",
    )

    # ── Recommendations ──
    recommended_pois: list[ScoredPOI] = Field(
        default_factory=list,
        description="All recommended POIs with scores, across all categories",
    )

    daily_clusters: list[DailyCluster] = Field(
        default_factory=list,
        description="POIs grouped into daily clusters by area/theme",
    )

    # ── Must-visit handling ──
    must_visit_status: list[ScoredPOI] = Field(
        default_factory=list,
        description="User's must-visit places with feasibility assessment",
    )
    skipped_must_visits: list[str] = Field(
        default_factory=list,
        description="Must-visit places that could not be included (with reasons)",
    )

    # ── Category summaries ──
    top_attractions: list[ScoredPOI] = Field(
        default_factory=list,
        description="Top recommended attractions",
    )
    top_restaurants: list[ScoredPOI] = Field(
        default_factory=list,
        description="Top recommended restaurants",
    )
    top_accommodations: list[ScoredPOI] = Field(
        default_factory=list,
        description="Top recommended hotels/accommodations",
    )

    # ── Reasoning ──
    reasoning_details: list[str] = Field(
        default_factory=list,
        description="Detailed reasoning for the recommendation choices",
    )
    trade_offs: list[str] = Field(
        default_factory=list,
        description="Trade-offs that were considered, e.g. 'A评分更高但B更近'",
    )

    # ── Warnings ──
    warnings: list[str] = Field(
        default_factory=list,
        description="Issues users should be aware of",
    )

    # ── Display helpers ──

    @property
    def total_recommendations(self) -> int:
        return len(self.recommended_pois)

    @property
    def display_summary(self) -> str:
        parts = [f"📊 共推荐 {self.total_recommendations} 个地点"]
        if self.daily_clusters:
            parts.append(f"📅 规划了 {len(self.daily_clusters)} 天")
        if self.top_restaurants:
            parts.append(f"🍽️ {len(self.top_restaurants)} 家餐厅推荐")
        if self.top_attractions:
            parts.append(f"🏛️ {len(self.top_attractions)} 个景点推荐")
        return " | ".join(parts)

    def get_top_pois(self, n: int = 5) -> list[ScoredPOI]:
        """Return the top-N highest-scored POIs."""
        sorted_pois = sorted(self.recommended_pois, key=lambda x: x.score, reverse=True)
        return sorted_pois[:n]
