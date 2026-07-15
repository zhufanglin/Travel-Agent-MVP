"""Analyst Agent — filters, scores, and clusters research data.

Analyzes the ResearchReport against user preferences to produce
ranked recommendations and daily clusters for the Planner.
"""

from itertools import cycle

from travel_agent.graph.state import GraphState
from travel_agent.schemas.analysis import AnalysisResult, DailyCluster, ScoredPOI
from travel_agent.schemas.common import POICategory
from travel_agent.schemas.research import ResearchReport
from travel_agent.schemas.travel import TravelIntent


def _score_poi(
    poi_category: POICategory,
    poi_rating: float,
    preferences_interests: list,
    must_visit: list[str],
    poi_name: str,
) -> tuple[float, list[str], list[str]]:
    """Score a POI based on user preferences.

    Returns:
        Tuple of (score, match_reasons, concerns).
    """
    score = 5.0  # base score
    reasons = []
    concerns = []

    # Boost for matching interests
    if poi_category in preferences_interests or not preferences_interests:
        score += 2.0
        reasons.append(f"符合兴趣: {poi_category.label_cn}")

    # Boost for high ratings
    if poi_rating and poi_rating >= 4.5:
        score += 1.5
        reasons.append(f"评分高 ({poi_rating})")
    elif poi_rating and poi_rating >= 4.0:
        score += 0.8
        reasons.append(f"评分不错 ({poi_rating})")
    elif poi_rating and poi_rating < 3.5:
        score -= 1.0
        concerns.append(f"评分较低 ({poi_rating})")

    # Must-visit bonus
    if any(v in poi_name for v in must_visit):
        score += 2.0
        reasons.append("用户指定必去")

    # Cap at 10
    score = max(0, min(10, score))

    return score, reasons, concerns


def _cluster_pois(
    scored_pois: list[ScoredPOI],
    days: int,
    destination: str,
) -> list[DailyCluster]:
    """Group scored POIs into daily clusters.

    Simple clustering: distribute POIs across days, grouping by category.
    """
    if not scored_pois:
        return []

    # Sort by score descending, then round-robin assign to days
    sorted_pois = sorted(scored_pois, key=lambda x: x.score, reverse=True)

    # Group POIs by category
    attraction_pois = [p for p in sorted_pois if p.poi.category in (
        POICategory.ATTRACTION, POICategory.MUSEUM, POICategory.PARK)]
    food_pois = [p for p in sorted_pois if p.poi.category == POICategory.RESTAURANT]
    other_pois = [p for p in sorted_pois if p.poi.category not in (
        POICategory.ATTRACTION, POICategory.MUSEUM, POICategory.PARK, POICategory.RESTAURANT)]

    clusters: list[DailyCluster] = []
    day_themes = cycle([
        f"{destination}经典探索",
        f"{destination}深度体验",
        f"{destination}休闲时光",
        f"{destination}文化之旅",
        f"{destination}自由安排",
    ])

    for day in range(days):
        # Each day: 2-3 attractions, 1-2 restaurants, 1 other
        day_pois: list[ScoredPOI] = []
        for pool, count in [(attraction_pois, 3), (food_pois, 2), (other_pois, 1)]:
            for _ in range(count):
                if pool:
                    day_pois.append(pool.pop(0))

        if not day_pois:
            day_pois.append(sorted_pois[day % len(sorted_pois)])
            day_pois[-1].score -= 1  # less ideal placement

        cluster = DailyCluster(
            day_index=day,
            label=f"第{day + 1}天: {next(day_themes)}",
            pois=day_pois,
        )
        clusters.append(cluster)

    return clusters


def analyst_node(state: GraphState) -> dict:
    """Analyze research report and produce recommendations.

    Args:
        state: Current GraphState with travel_intent and research_report.

    Returns:
        Updated state with analysis_result.
    """
    intent: TravelIntent = state.get("travel_intent")
    report: ResearchReport = state.get("research_report")

    if not report:
        return {
            "errors": state.get("errors", []) + ["Analyst: no research_report in state"],
            "current_phase": "error",
        }

    if not report.pois.all_pois:
        return {
            "analysis_result": AnalysisResult(
                summary=f"抱歉，在{intent.destination if intent else '目的地'}未找到相关推荐。请尝试调整偏好。",
                warnings=["未找到匹配的兴趣点"],
            ),
            "current_phase": "plan",
        }

    preferences = intent.preferences if intent else None
    interests = list(preferences.interests) if preferences and preferences.interests else []
    must_visit = list(intent.constraints.must_visit) if intent and intent.constraints else []

    # ── Score all POIs ──
    scored_pois: list[ScoredPOI] = []
    for poi in report.pois.all_pois:
        score, reasons, concerns = _score_poi(
            poi_category=poi.category,
            poi_rating=poi.rating or 0,
            preferences_interests=interests,
            must_visit=must_visit,
            poi_name=poi.name,
        )
        scored_pois.append(ScoredPOI(
            poi=poi,
            score=score,
            match_reasons=reasons,
            concerns=concerns,
        ))

    scored_pois.sort(key=lambda x: x.score, reverse=True)

    # ── Categorize ──
    top_attractions = [s for s in scored_pois if s.poi.category in (
        POICategory.ATTRACTION, POICategory.MUSEUM, POICategory.PARK)][:5]
    top_restaurants = [s for s in scored_pois if s.poi.category == POICategory.RESTAURANT][:5]
    top_hotels = [s for s in scored_pois if s.poi.category == POICategory.HOTEL][:3]

    # ── Cluster by day ──
    days = intent.duration_days if intent and intent.duration_days else 3
    dest = intent.destination if intent and intent.destination else "目的地"
    daily_clusters = _cluster_pois(scored_pois, days, dest)

    # ── Must-visit check ──
    must_visit_status = [s for s in scored_pois if any(v in s.poi.name for v in must_visit)]
    found_names = {s.poi.name for s in must_visit_status}
    skipped = [v for v in must_visit if not any(v in n for n in found_names)]

    # ── Build result ──
    summary = f"根据你的偏好，从{len(report.pois.all_pois)}个地点中筛选出{len(scored_pois)}个推荐。"
    if top_attractions:
        summary += f" 顶级的{len(top_attractions)}个景点已标记。"
    if top_restaurants:
        summary += f" 推荐{len(top_restaurants)}家餐厅。"
    if skipped:
        summary += f" 有{len(skipped)}个指定地点未能纳入（{', '.join(skipped)}）。"

    result = AnalysisResult(
        summary=summary,
        recommended_pois=scored_pois,
        daily_clusters=daily_clusters,
        top_attractions=top_attractions,
        top_restaurants=top_restaurants,
        top_accommodations=top_hotels,
        must_visit_status=must_visit_status,
        skipped_must_visits=skipped,
        reasoning_details=[
            f"基于{c.label_cn}偏好筛选" for c in interests
        ] if interests else ["基于评分排序"],
    )

    return {
        "analysis_result": result,
        "current_phase": "plan",
    }
