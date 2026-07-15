"""Research report model — raw data collected by the Researcher Agent.

The Researcher Agent uses external tools (weather, LBS, routing) to
gather factual information. Every field in this report should be traceable
to a specific tool call. No LLM-generated "facts" should appear here.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from travel_agent.schemas.common import (
    DayForecast,
    GeoLocation,
    POI,
    Route,
)


class WeatherReport(BaseModel):
    """Aggregated weather information for the trip period."""

    forecasts: list[DayForecast] = Field(
        default_factory=list,
        description="Daily weather forecasts covering the trip period",
    )
    overall_summary: str = Field(
        default="",
        description="Natural language summary of overall weather trend",
    )
    source: str = Field(default="", description="Weather data source")

    @property
    def display(self) -> str:
        lines = [f.display for f in self.forecasts]
        return " | ".join(lines) if lines else "暂无天气数据"


class POISearchResult(BaseModel):
    """Collection of POIs from LBS search, grouped by category."""

    all_pois: list[POI] = Field(
        default_factory=list,
        description="All POIs found across all categories",
    )
    source: str = Field(default="", description="LBS data source")
    searched_categories: list[str] = Field(
        default_factory=list,
        description="Which POI categories were searched",
    )

    @property
    def count(self) -> int:
        return len(self.all_pois)

    @property
    def grouped_by_category(self) -> dict[str, list[POI]]:
        """Return POIs grouped by category for Streamlit display."""
        groups: dict[str, list[POI]] = {}
        for poi in self.all_pois:
            cat = poi.category.label_cn
            if cat not in groups:
                groups[cat] = []
            groups[cat].append(poi)
        return groups


class TransportationReport(BaseModel):
    """Transportation and routing information."""

    routes_from_origin: Optional[list[Route]] = Field(
        default=None,
        description="Routes from departure city to destination",
    )
    local_transport_options: list[Route] = Field(
        default_factory=list,
        description="Local transportation info and sample routes",
    )
    source: str = Field(default="", description="Routing data source")


class ResearchMetadata(BaseModel):
    """Tracking metadata for research completeness."""

    started_at: datetime = Field(default_factory=datetime.now, description="Research start time")
    completed_at: Optional[datetime] = Field(default=None, description="Research end time")
    tools_called: list[str] = Field(default_factory=list, description="Tools that were invoked")
    failed_tools: list[str] = Field(default_factory=list, description="Tools that failed")
    data_coverage: dict[str, bool] = Field(
        default_factory=dict,
        description="Which data categories were successfully retrieved",
    )

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def all_successful(self) -> bool:
        return len(self.failed_tools) == 0


class ResearchReport(BaseModel):
    """Complete research output from the Researcher Agent.

    This is the ONLY source of factual data in the system.
    Analyst and Planner agents must derive all recommendations
    and plans from this report — they may NOT call external tools
    or invent data.
    """

    # ── Destination context ──
    destination_info: GeoLocation = Field(
        ...,  # required
        description="Geocoded destination location",
    )

    # ── Core data sections ──
    weather: WeatherReport = Field(
        default_factory=WeatherReport,
        description="Weather forecasts for trip period",
    )
    pois: POISearchResult = Field(
        default_factory=POISearchResult,
        description="Points of interest search results",
    )
    transportation: TransportationReport = Field(
        default_factory=TransportationReport,
        description="Transportation and routing info",
    )

    # ── Metadata ──
    metadata: ResearchMetadata = Field(
        default_factory=ResearchMetadata,
        description="Research tracking metadata",
    )

    # ── Quality control ──
    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings about data quality or missing data",
    )

    # ── Display helpers ──

    @property
    def display_summary(self) -> str:
        """Return a compact summary of research findings."""
        parts = [f"📍 {self.destination_info.name}"]
        if self.weather.forecasts:
            dates = f"{self.weather.forecasts[0].forecast_date} ~ {self.weather.forecasts[-1].forecast_date}"
            parts.append(f"🌤️ {dates}")
        parts.append(f"🏪 找到 {self.pois.count} 个兴趣点")
        if self.warnings:
            parts.append(f"⚠️ {len(self.warnings)} 条警告")
        return " | ".join(parts)

    def get_pois_by_category(self, category_name: str) -> list[POI]:
        """Filter POIs by category label for display."""
        return [p for p in self.pois.all_pois if p.category.value == category_name]

    def get_weather_for_date(self, target_date: date) -> Optional[DayForecast]:
        """Look up the forecast for a specific date."""
        for f in self.weather.forecasts:
            if f.forecast_date == target_date:
                return f
        return None
