"""Common data models used across all schemas.

These types serve as building blocks for inter-agent communication.
Each model is designed with Streamlit display in mind —
fields include display-ready labels, emoji markers, and formatted strings.
"""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
#  Enums
# ──────────────────────────────────────────────


class POICategory(str, Enum):
    """Categories of Points of Interest."""

    ATTRACTION = "attraction"        # 景点/景区
    RESTAURANT = "restaurant"        # 餐厅/美食
    HOTEL = "hotel"                  # 住宿
    SHOPPING = "shopping"            # 购物
    TRANSPORT = "transport"          # 交通枢纽
    ENTERTAINMENT = "entertainment"  # 娱乐场所
    MUSEUM = "museum"               # 博物馆/文化场馆
    PARK = "park"                    # 公园/自然风光
    NIGHTLIFE = "nightlife"         # 夜生活
    OTHER = "other"                  # 其他

    @property
    def label_cn(self) -> str:
        labels = {
            "attraction": "景点",
            "restaurant": "美食",
            "hotel": "住宿",
            "shopping": "购物",
            "transport": "交通",
            "entertainment": "娱乐",
            "museum": "文化场馆",
            "park": "公园",
            "nightlife": "夜生活",
            "other": "其他",
        }
        return labels[self.value]

    @property
    def emoji(self) -> str:
        icons = {
            "attraction": "🏛️",
            "restaurant": "🍽️",
            "hotel": "🏨",
            "shopping": "🛍️",
            "transport": "🚉",
            "entertainment": "🎪",
            "museum": "🏛️",
            "park": "🌳",
            "nightlife": "🌙",
            "other": "📍",
        }
        return icons[self.value]


class TravelMode(str, Enum):
    """Transportation modes for route planning."""

    WALKING = "walking"
    DRIVING = "driving"
    PUBLIC_TRANSIT = "public_transit"
    TAXI = "taxi"
    BICYCLING = "bicycling"

    @property
    def label_cn(self) -> str:
        labels = {
            "walking": "步行",
            "driving": "驾车",
            "public_transit": "公共交通",
            "taxi": "出租车",
            "bicycling": "骑行",
        }
        return labels[self.value]

    @property
    def emoji(self) -> str:
        icons = {
            "walking": "🚶",
            "driving": "🚗",
            "public_transit": "🚌",
            "taxi": "🚕",
            "bicycling": "🚲",
        }
        return icons[self.value]


class WeatherCondition(str, Enum):
    """Weather condition categories."""

    SUNNY = "sunny"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    RAINY = "rainy"
    SNOWY = "snowy"
    WINDY = "windy"
    FOGGY = "foggy"
    THUNDERSTORM = "thunderstorm"

    @property
    def label_cn(self) -> str:
        labels = {
            "sunny": "晴",
            "cloudy": "多云",
            "overcast": "阴",
            "rainy": "雨",
            "snowy": "雪",
            "windy": "风",
            "foggy": "雾",
            "thunderstorm": "雷暴",
        }
        return labels[self.value]

    @property
    def emoji(self) -> str:
        icons = {
            "sunny": "☀️",
            "cloudy": "⛅",
            "overcast": "☁️",
            "rainy": "🌧️",
            "snowy": "❄️",
            "windy": "💨",
            "foggy": "🌫️",
            "thunderstorm": "⛈️",
        }
        return icons[self.value]


class BudgetLevel(str, Enum):
    """Budget level classification."""

    ECONOMY = "economy"        # 经济
    COMFORT = "comfort"        # 舒适
    LUXURY = "luxury"          # 豪华

    @property
    def label_cn(self) -> str:
        labels = {
            "economy": "经济型",
            "comfort": "舒适型",
            "luxury": "豪华型",
        }
        return labels[self.value]

    @property
    def emoji(self) -> str:
        icons = {
            "economy": "💵",
            "comfort": "💰",
            "luxury": "💎",
        }
        return icons[self.value]


class MealType(str, Enum):
    """Meal time classification."""

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"

    @property
    def label_cn(self) -> str:
        labels = {
            "breakfast": "早餐",
            "lunch": "午餐",
            "dinner": "晚餐",
            "snack": "小吃",
        }
        return labels[self.value]


# ──────────────────────────────────────────────
#  Value Objects
# ──────────────────────────────────────────────


class Coordinate(BaseModel):
    """Geographic coordinate (WGS-84)."""

    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")

    @property
    def display(self) -> str:
        return f"{self.lat:.4f}, {self.lng:.4f}"


class GeoLocation(BaseModel):
    """Resolved geographic location with address info."""

    name: str = Field(..., description="Location name")
    address: str = Field(default="", description="Full address string")
    coordinate: Coordinate = Field(..., description="Geographic coordinates")
    city: str = Field(default="", description="City name")
    district: str = Field(default="", description="District / area name")
    formatted: str = Field(default="", description="Display-ready full location string")

    @property
    def short_display(self) -> str:
        return f"{self.name} ({self.city})"


class TimeSlot(BaseModel):
    """A time slot within a day."""

    start_time: str = Field(..., description="Start time, HH:MM format", pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., description="End time, HH:MM format", pattern=r"^\d{2}:\d{2}$")
    label: str = Field(default="", description="Human-readable label, e.g. '上午'")

    @property
    def display(self) -> str:
        return f"{self.start_time} - {self.end_time}"


class Budget(BaseModel):
    """Budget specification."""

    min_amount: float = Field(default=0, ge=0, description="Minimum budget")
    max_amount: float = Field(default=0, ge=0, description="Maximum budget (0 = no limit)")
    currency: str = Field(default="CNY", description="Currency code")
    level: Optional[BudgetLevel] = Field(default=None, description="Budget level classification")

    @property
    def display(self) -> str:
        if self.max_amount > 0:
            return f"¥{self.min_amount:,.0f} - ¥{self.max_amount:,.0f}"
        if self.min_amount > 0:
            return f"¥{self.min_amount:,.0f}+"
        return "未设定"


class DayForecast(BaseModel):
    """Weather forecast for a single day."""

    forecast_date: date = Field(..., alias="date", description="Forecast date")
    condition: WeatherCondition = Field(..., description="Weather condition")
    temperature_high: float = Field(..., description="High temperature (°C)")
    temperature_low: float = Field(..., description="Low temperature (°C)")
    humidity: Optional[float] = Field(default=None, description="Humidity percentage")
    wind_speed: Optional[float] = Field(default=None, description="Wind speed")
    precipitation_probability: Optional[float] = Field(
        default=None, ge=0, le=100, description="Rain probability (%)"
    )
    description: str = Field(default="", description="Human-readable weather description")

    @property
    def display(self) -> str:
        return (
            f"{self.forecast_date.isoformat()} {self.condition.emoji} "
            f"{self.temperature_low:.0f}~{self.temperature_high:.0f}°C"
        )

    @property
    def summary(self) -> str:
        return (
            f"{self.forecast_date.strftime('%m/%d')} {self.condition.emoji} "
            f"{self.temperature_low:.0f}-{self.temperature_high:.0f}°C"
        )


class POI(BaseModel):
    """Point of Interest — raw data from LBS service."""

    poi_id: str = Field(default="", description="Original ID from LBS provider")
    name: str = Field(..., description="POI name")
    category: POICategory = Field(..., description="POI category")
    subcategory: str = Field(default="", description="Fine-grained category, e.g. '川菜', '博物馆'")
    location: GeoLocation = Field(..., description="Geographic location")
    rating: Optional[float] = Field(default=None, ge=0, le=5, description="Average rating (0-5)")
    price_level: Optional[int] = Field(default=None, ge=1, le=5, description="Price level (1-5)")
    avg_cost: Optional[float] = Field(default=None, ge=0, description="Estimated cost per person")
    opening_hours: Optional[str] = Field(
        default=None, description="Opening hours text, e.g. '09:00-17:00'"
    )
    phone: Optional[str] = Field(default=None, description="Contact phone")
    website: Optional[str] = Field(default=None, description="Website URL")
    image_url: Optional[str] = Field(default=None, description="POI image URL")
    description: str = Field(default="", description="Brief description")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering/labeling")
    source: str = Field(default="", description="Data source identifier")

    @property
    def display_rating(self) -> str:
        if self.rating is None:
            return "暂无评分"
        stars = "⭐" * round(self.rating)
        return f"{stars} {self.rating:.1f}"

    @property
    def display_price(self) -> str:
        if self.avg_cost is not None:
            return f"约 ¥{self.avg_cost:.0f}/人"
        if self.price_level is not None:
            return "💰" * self.price_level
        return ""

    @property
    def display_name(self) -> str:
        return f"{self.category.emoji} {self.name}"


class RouteStep(BaseModel):
    """A single step in a route's turn-by-turn directions.

    Defined before Route to avoid forward-reference issues.
    """

    instruction: str = Field(..., description="Navigation instruction")
    distance_meters: float = Field(default=0, description="Step distance in meters")
    duration_minutes: float = Field(default=0, description="Step duration in minutes")
    mode: TravelMode = Field(default=TravelMode.WALKING, description="Transport mode for this step")
    start_location: Optional[Coordinate] = Field(default=None, description="Step start coordinate")
    end_location: Optional[Coordinate] = Field(default=None, description="Step end coordinate")

    @property
    def display(self) -> str:
        duration = f"{int(self.duration_minutes)}分钟" if self.duration_minutes else ""
        return f"{self.mode.emoji} {self.instruction} ({duration})"


class Route(BaseModel):
    """Transportation route between two points."""

    origin: GeoLocation = Field(..., description="Start point")
    destination: GeoLocation = Field(..., description="End point")
    mode: TravelMode = Field(..., description="Transport mode")
    distance_meters: Optional[float] = Field(default=None, description="Total distance in meters")
    duration_minutes: Optional[float] = Field(default=None, description="Estimated duration in minutes")
    steps: list[RouteStep] = Field(default_factory=list, description="Turn-by-turn directions")
    cost_estimate: Optional[float] = Field(default=None, ge=0, description="Estimated cost")
    polyline: Optional[str] = Field(default=None, description="Encoded polyline for map display")

    @property
    def display_distance(self) -> str:
        if self.distance_meters is None:
            return ""
        if self.distance_meters >= 1000:
            return f"{self.distance_meters / 1000:.1f} km"
        return f"{self.distance_meters:.0f} m"

    @property
    def display_duration(self) -> str:
        if self.duration_minutes is None:
            return ""
        if self.duration_minutes >= 60:
            hours = int(self.duration_minutes // 60)
            mins = int(self.duration_minutes % 60)
            return f"{hours}小时{mins}分钟"
        return f"{int(self.duration_minutes)}分钟"

    @property
    def summary(self) -> str:
        return f"{self.mode.emoji} {self.display_duration} ({self.display_distance})"
