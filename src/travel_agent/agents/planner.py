"""Planner Agent — creates the final day-by-day travel itinerary.

Takes the AnalysisResult and user TravelIntent to produce a structured
TravelPlan with daily schedules, budget breakdown, and practical notes.
"""

from datetime import date, timedelta

from travel_agent.graph.state import GraphState
from travel_agent.schemas.analysis import AnalysisResult, DailyCluster, ScoredPOI
from travel_agent.schemas.research import ResearchReport
from travel_agent.schemas.common import MealType, POICategory, TimeSlot
from travel_agent.schemas.plan import (
    Activity,
    BudgetBreakdown,
    DayPlan,
    MealPlan,
    TravelPlan,
)
from travel_agent.schemas.travel import TravelIntent
from travel_agent.tools.registry import call_tool as tool


def _build_day_plan(
    cluster: DailyCluster,
    cluster_date: date,
    destination: str,
    budget_breakdown: BudgetBreakdown,
) -> DayPlan:
    """Convert a DailyCluster into a DayPlan with time slots and meals."""
    activities: list[Activity] = []
    meals: list[MealPlan] = []
    tips: list[str] = []

    # Morning activity (09:00-12:00)
    morning_pois = [p for p in cluster.pois if p.poi.category in (
        POICategory.ATTRACTION, POICategory.MUSEUM, POICategory.PARK)]
    afternoon_pois = [p for p in cluster.pois if p not in morning_pois]

    # Assign time slots
    time_slots = [
        ("09:00", "12:00", "上午"),
        ("13:00", "17:00", "下午"),
        ("19:00", "21:00", "晚上"),
    ]

    assigned_count = 0
    for i, (start, end, label) in enumerate(time_slots):
        if i == 0 and morning_pois:
            poi_ref = morning_pois[assigned_count % len(morning_pois)]
        elif i == 1 and afternoon_pois:
            offset = assigned_count
            poi_ref = afternoon_pois[offset % len(afternoon_pois)]
        elif i == 2:
            selected = [p for p in cluster.pois if p not in activities]
            poi_ref = selected[assigned_count % len(cluster.pois)] if cluster.pois else cluster.pois[0]
            if poi_ref.poi.category == POICategory.RESTAURANT:
                meals.append(MealPlan(
                    meal_type=MealType.DINNER,
                    suggestion=f"在{poi_ref.poi.name}用餐",
                    location=poi_ref.poi.location,
                    estimated_cost=poi_ref.poi.avg_cost,
                    cuisine_type=poi_ref.poi.subcategory,
                ))
                continue
        else:
            break

        act = Activity(
            name=poi_ref.poi.name,
            description=poi_ref.poi.description or f"探索{poi_ref.poi.name}",
            location=poi_ref.poi.location,
            category=poi_ref.poi.category,
            time_slot=TimeSlot(start_time=start, end_time=end, label=label),
            estimated_cost=poi_ref.poi.avg_cost,
            tags=poi_ref.poi.tags,
        )
        activities.append(act)
        assigned_count += 1

        # Add meal suggestions around noon and evening
        if i == 0:
            meals.append(MealPlan(
                meal_type=MealType.LUNCH,
                suggestion=f"在附近餐厅解决午餐",
                estimated_cost=60,
            ))
        elif i == 1:
            meals.append(MealPlan(
                meal_type=MealType.DINNER,
                suggestion="品尝当地特色美食",
                estimated_cost=80,
            ))

    # Extract tips from POI concerns
    for poi_ref in cluster.pois:
        if poi_ref.concerns:
            tips.extend(poi_ref.concerns)

    # Weather-based tips
    tips.append("建议查看当日天气预报，合理安排出行")

    # Calculate daily budget proportionally
    daily_budget = round(budget_breakdown.total_estimated / max(len(cluster.pois), 1))

    return DayPlan(
        day_index=cluster.day_index,
        title=cluster.label,
        date=cluster_date.isoformat() if cluster_date else "",
        activities=activities,
        meals=meals,
        tips=tips[:5],
        daily_budget_estimate=float(daily_budget),
    )


def planner_node(state: GraphState) -> dict:
    """Create a complete travel plan from analysis results.

    Args:
        state: Current GraphState with travel_intent and analysis_result.

    Returns:
        Updated state with travel_plan.
    """
    intent: TravelIntent = state.get("travel_intent")
    analysis: AnalysisResult = state.get("analysis_result")
    research: ResearchReport = state.get("research_report")

    if not analysis:
        return {
            "errors": state.get("errors", []) + ["Planner: no analysis_result in state"],
            "current_phase": "error",
        }

    # Derive destination from best available source
    dest = "目的地"
    if intent and intent.destination:
        dest = intent.destination
    elif research and research.destination_info:
        dest = research.destination_info.name
    days = intent.duration_days if intent and intent.duration_days else 3
    start_date = intent.start_date if intent and intent.start_date else date.today()
    companions = intent.companions if intent else 1

    # ── Estimate budget ──
    budget = tool(
        "planner", "estimate_budget",
        days=days,
        preferences=intent.preferences if intent else None,
        companions=companions,
    )

    # ── Build day plans ──
    day_plans: list[DayPlan] = []
    clusters = analysis.daily_clusters

    if not clusters and analysis.recommended_pois:
        # No clusters but we have POIs — create a simple daily distribution
        total_pois = len(analysis.recommended_pois)
        pois_per_day = max(1, total_pois // days)
        for d in range(days):
            start_idx = d * pois_per_day
            end_idx = start_idx + pois_per_day if d < days - 1 else total_pois
            cluster = DailyCluster(
                day_index=d,
                label=f"第{d + 1}天: {dest}探索",
                pois=analysis.recommended_pois[start_idx:end_idx],
            )
            current_date = start_date + timedelta(days=d)
            day_plans.append(_build_day_plan(cluster, current_date, dest, budget))

    elif clusters:
        for cluster in clusters:
            current_date = start_date + timedelta(days=cluster.day_index)
            day_plans.append(_build_day_plan(cluster, current_date, dest, budget))

    # ── Assemble plan ──
    overview = f"{days}天{dest}之旅，适合{companions}人出行。"
    if analysis.summary:
        overview += f" {analysis.summary}"

    plan = TravelPlan(
        title=f"{dest}{days}日游",
        destination=dest,
        days=day_plans,
        budget_breakdown=budget,
        overview=overview,
        notes=[
            "建议提前预订酒店和热门景点门票",
            "出行前查看当地天气，准备合适衣物",
            "下载当地地图App方便导航",
        ],
        packing_tips=[
            "身份证/护照",
            "手机充电器/移动电源",
            "常用药品",
        ],
    )

    return {
        "travel_plan": plan,
        "current_phase": "complete",
    }
