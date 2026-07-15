"""Mock weather tool — returns realistic weather forecasts.

MVP uses mock data. Structure matches travel_agent.schemas.research.WeatherReport.
Replace with real API calls in Phase 2.
"""

from datetime import date, timedelta
from random import choice, randint

from travel_agent.schemas.common import DayForecast, WeatherCondition
from travel_agent.schemas.research import WeatherReport

_CITY_WEATHER = {
    "北京": {
        "summer": {"high": (30, 38), "low": (22, 28), "conditions": [WeatherCondition.SUNNY, WeatherCondition.CLOUDY]},
        "winter": {"high": (-2, 6), "low": (-10, -2), "conditions": [WeatherCondition.CLOUDY, WeatherCondition.SUNNY, WeatherCondition.SNOWY]},
        "spring": {"high": (15, 25), "low": (5, 15), "conditions": [WeatherCondition.CLOUDY, WeatherCondition.SUNNY, WeatherCondition.WINDY]},
        "autumn": {"high": (18, 26), "low": (8, 16), "conditions": [WeatherCondition.SUNNY, WeatherCondition.CLOUDY]},
    },
    "上海": {
        "summer": {"high": (32, 39), "low": (25, 30), "conditions": [WeatherCondition.SUNNY, WeatherCondition.CLOUDY, WeatherCondition.RAINY]},
        "winter": {"high": (4, 10), "low": (-1, 4), "conditions": [WeatherCondition.CLOUDY, WeatherCondition.RAINY]},
        "spring": {"high": (16, 24), "low": (8, 15), "conditions": [WeatherCondition.RAINY, WeatherCondition.CLOUDY, WeatherCondition.SUNNY]},
        "autumn": {"high": (18, 26), "low": (12, 18), "conditions": [WeatherCondition.SUNNY, WeatherCondition.CLOUDY]},
    },
    "广州": {
        "summer": {"high": (32, 36), "low": (25, 28), "conditions": [WeatherCondition.SUNNY, WeatherCondition.RAINY, WeatherCondition.THUNDERSTORM]},
        "winter": {"high": (16, 22), "low": (10, 15), "conditions": [WeatherCondition.CLOUDY, WeatherCondition.SUNNY]},
        "spring": {"high": (22, 28), "low": (16, 22), "conditions": [WeatherCondition.RAINY, WeatherCondition.CLOUDY]},
        "autumn": {"high": (24, 30), "low": (18, 24), "conditions": [WeatherCondition.SUNNY, WeatherCondition.CLOUDY]},
    },
    "成都": {
        "summer": {"high": (28, 34), "low": (20, 25), "conditions": [WeatherCondition.CLOUDY, WeatherCondition.RAINY]},
        "winter": {"high": (8, 14), "low": (2, 8), "conditions": [WeatherCondition.CLOUDY, WeatherCondition.RAINY]},
        "spring": {"high": (16, 24), "low": (10, 16), "conditions": [WeatherCondition.RAINY, WeatherCondition.CLOUDY, WeatherCondition.SUNNY]},
        "autumn": {"high": (18, 26), "low": (12, 18), "conditions": [WeatherCondition.SUNNY, WeatherCondition.CLOUDY]},
    },
    "杭州": {
        "summer": {"high": (30, 38), "low": (24, 28), "conditions": [WeatherCondition.SUNNY, WeatherCondition.CLOUDY, WeatherCondition.RAINY]},
        "winter": {"high": (5, 12), "low": (0, 5), "conditions": [WeatherCondition.CLOUDY, WeatherCondition.RAINY]},
        "spring": {"high": (16, 24), "low": (8, 15), "conditions": [WeatherCondition.RAINY, WeatherCondition.CLOUDY, WeatherCondition.SUNNY]},
        "autumn": {"high": (18, 26), "low": (12, 18), "conditions": [WeatherCondition.SUNNY, WeatherCondition.CLOUDY]},
    },
}

_DEFAULT_CITY = "北京"

_DESCRIPTIONS = {
    WeatherCondition.SUNNY: "晴空万里，阳光充足",
    WeatherCondition.CLOUDY: "多云，适合户外活动",
    WeatherCondition.OVERCAST: "阴天，体感较凉",
    WeatherCondition.RAINY: "有降雨，建议携带雨具",
    WeatherCondition.SNOWY: "有降雪，注意保暖",
    WeatherCondition.WINDY: "风力较大，注意防风",
    WeatherCondition.FOGGY: "有雾，能见度较低",
    WeatherCondition.THUNDERSTORM: "雷阵雨，注意安全",
}


def _get_season(month: int) -> str:
    if 3 <= month <= 5:
        return "spring"
    if 6 <= month <= 8:
        return "summer"
    if 9 <= month <= 11:
        return "autumn"
    return "winter"


def get_weather(destination: str, start_date: date, end_date: date) -> WeatherReport:
    """Get mock weather forecast for a destination and date range.

    Args:
        destination: City name in Chinese.
        start_date: First day of the trip.
        end_date: Last day of the trip.

    Returns:
        WeatherReport containing daily forecasts and summary.
    """
    city_data = _CITY_WEATHER.get(destination, _CITY_WEATHER[_DEFAULT_CITY])

    forecasts: list[DayForecast] = []
    current = start_date
    while current <= end_date:
        season = _get_season(current.month)
        season_data = city_data[season]
        condition = choice(season_data["conditions"])
        temp_high = randint(*season_data["high"])
        temp_low = randint(*season_data["low"])
        if temp_low > temp_high:
            temp_low, temp_high = temp_high, temp_low

        forecast = DayForecast(
            date=current.isoformat(),
            condition=condition,
            temperature_high=float(temp_high),
            temperature_low=float(temp_low),
            humidity=randint(40, 90),
            precipitation_probability=randint(5, 80) if condition in (WeatherCondition.RAINY, WeatherCondition.THUNDERSTORM, WeatherCondition.SNOWY) else randint(0, 20),
            description=_DESCRIPTIONS.get(condition, ""),
        )
        forecasts.append(forecast)
        current += timedelta(days=1)

    # Generate summary from first forecast
    first = forecasts[0]
    overall = f"{destination}{start_date}至{end_date}天气预报："
    overall += f"以{first.condition.label_cn}为主，{first.description}。"
    if any(f.condition in (WeatherCondition.RAINY, WeatherCondition.THUNDERSTORM) for f in forecasts):
        overall += " 部分日期有降雨，建议携带雨具。"
    if all(f.condition == WeatherCondition.SUNNY for f in forecasts):
        overall += " 适合户外活动，注意防晒。"

    report = WeatherReport()
    report.forecasts = forecasts
    report.overall_summary = overall
    report.source = "mock-weather-service"
    report.model_config["from_attributes"] = True

    return report
