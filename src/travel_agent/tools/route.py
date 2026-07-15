"""Mock route calculation tool — returns sample transportation routes.

MVP uses mock data. Structure matches travel_agent.schemas.common.Route.
Replace with real navigation API (Amap / Baidu Maps) in Phase 2.
"""

from random import choice, randint
from typing import Optional

from travel_agent.schemas.common import (
    Coordinate,
    GeoLocation,
    Route,
    RouteStep,
    TravelMode,
)


def _estimate_duration(distance_m: float, mode: TravelMode) -> float:
    """Rough duration estimate in minutes."""
    speeds = {
        TravelMode.WALKING: 80,
        TravelMode.DRIVING: 600,
        TravelMode.TAXI: 500,
        TravelMode.PUBLIC_TRANSIT: 300,
        TravelMode.BICYCLING: 200,
    }
    speed_m_per_min = speeds.get(mode, 300)
    return distance_m / speed_m_per_min


def _generate_steps(
    origin: GeoLocation,
    destination: GeoLocation,
    mode: TravelMode,
) -> list[RouteStep]:
    """Generate plausible turn-by-turn steps."""
    steps = [
        RouteStep(
            instruction=f"从{origin.name}出发",
            distance_meters=100,
            duration_minutes=2,
            mode=TravelMode.WALKING,
            start_location=origin.coordinate,
        ),
    ]

    if mode in (TravelMode.DRIVING, TravelMode.TAXI):
        steps.append(
            RouteStep(
                instruction=f"沿主干道行驶前往{destination.name}",
                distance_meters=randint(3000, 20000),
                duration_minutes=randint(15, 60),
                mode=mode,
            )
        )
    elif mode == TravelMode.PUBLIC_TRANSIT:
        steps.append(
            RouteStep(
                instruction=f"乘坐地铁前往{destination.name}方向",
                distance_meters=randint(5000, 30000),
                duration_minutes=randint(20, 50),
                mode=mode,
            )
        )
    elif mode == TravelMode.WALKING:
        steps.append(
            RouteStep(
                instruction=f"步行前往{destination.name}",
                distance_meters=randint(500, 3000),
                duration_minutes=randint(5, 40),
                mode=mode,
            )
        )
    elif mode == TravelMode.BICYCLING:
        steps.append(
            RouteStep(
                instruction=f"骑行前往{destination.name}",
                distance_meters=randint(1000, 5000),
                duration_minutes=randint(5, 25),
                mode=mode,
            )
        )

    steps.append(
        RouteStep(
            instruction=f"到达{destination.name}",
            distance_meters=50,
            duration_minutes=1,
            mode=TravelMode.WALKING,
            end_location=destination.coordinate,
        )
    )

    return steps


def calculate_route(
    origin: GeoLocation,
    destination: GeoLocation,
    mode: Optional[TravelMode] = None,
) -> Route:
    """Calculate a route between two locations.

    Args:
        origin: Starting location with coordinates.
        destination: Destination location with coordinates.
        mode: Preferred transport mode. If None, picks a reasonable default.

    Returns:
        Route object with steps, duration, and distance.
    """
    if mode is None:
        mode = choice([TravelMode.DRIVING, TravelMode.PUBLIC_TRANSIT, TravelMode.WALKING])

    # Rough distance from lat/lng (1 degree ≈ 111km)
    lat_diff = abs(destination.coordinate.lat - origin.coordinate.lat)
    lng_diff = abs(destination.coordinate.lng - origin.coordinate.lng)
    distance_m = (lat_diff + lng_diff) * 111_000 * randint(5, 15) // 10
    distance_m = max(distance_m, 500)

    duration = _estimate_duration(distance_m, mode)
    steps = _generate_steps(origin, destination, mode)

    return Route(
        origin=origin,
        destination=destination,
        mode=mode,
        distance_meters=float(distance_m),
        duration_minutes=duration,
        steps=steps,
        cost_estimate=duration * 2 if mode == TravelMode.TAXI else None,
    )
