"""Researcher Agent — gathers factual travel data via external tools and RAG.

Reads the TravelIntent and calls:
  1. Registered tools (weather, places, routing)
  2. RAG knowledge retriever (FAISS over Markdown travel guides)

All data sources are merged into a single ResearchReport.
"""

from datetime import date, timedelta
from typing import Optional

from travel_agent.graph.state import GraphState
from travel_agent.rag.retriever import KnowledgeRetriever
from travel_agent.schemas.common import Coordinate, GeoLocation
from travel_agent.schemas.research import (
    POISearchResult,
    ResearchMetadata,
    ResearchReport,
    TransportationReport,
    WeatherReport,
)
from travel_agent.tools.registry import call_tool as tool

# ── RAG retriever (lazy singleton — loads knowledge on first use) ──
_rag: Optional[KnowledgeRetriever] = None


def _get_rag() -> KnowledgeRetriever:
    global _rag
    if _rag is None:
        _rag = KnowledgeRetriever()
        _rag.build_index()
    return _rag


def _get_city_coordinates(city: str) -> Optional[GeoLocation]:
    """Look up a city's coordinates from known data."""
    city_map = {
        "北京": GeoLocation(name="北京", address="北京市", coordinate=Coordinate(lat=39.9042, lng=116.4074), city="北京"),
        "上海": GeoLocation(name="上海", address="上海市", coordinate=Coordinate(lat=31.2304, lng=121.4737), city="上海"),
        "广州": GeoLocation(name="广州", address="广州市", coordinate=Coordinate(lat=23.1291, lng=113.2644), city="广州"),
        "成都": GeoLocation(name="成都", address="成都市", coordinate=Coordinate(lat=30.5728, lng=104.0668), city="成都"),
        "深圳": GeoLocation(name="深圳", address="深圳市", coordinate=Coordinate(lat=22.5431, lng=114.0579), city="深圳"),
        "杭州": GeoLocation(name="杭州", address="杭州市", coordinate=Coordinate(lat=30.2741, lng=120.1551), city="杭州"),
        "西安": GeoLocation(name="西安", address="西安市", coordinate=Coordinate(lat=34.3416, lng=108.9398), city="西安"),
        "重庆": GeoLocation(name="重庆", address="重庆市", coordinate=Coordinate(lat=29.4316, lng=106.9123), city="重庆"),
    }
    return city_map.get(city)


def researcher_node(state: GraphState) -> dict:
    """Gather travel information by calling external tools.

    Args:
        state: Current GraphState with travel_intent.

    Returns:
        Updated state with research_report.
    """
    intent = state.get("travel_intent")
    if not intent:
        return {
            "current_phase": "error",
            "errors": ["Researcher: no travel_intent in state"],
        }

    dest = intent.destination or "北京"

    # If destination was missing, backfill it for downstream agents
    if not intent.destination:
        from copy import deepcopy
        intent = deepcopy(intent)
        intent.destination = dest

    # Date range
    days = intent.duration_days or 3
    start = intent.start_date or date.today()
    end = start + timedelta(days=days - 1)

    # ── 1. Get destination location ──
    geo = _get_city_coordinates(dest)
    if not geo:
        geo = GeoLocation(
            name=dest,
            address=dest,
            coordinate=Coordinate(lat=39.9042, lng=116.4074),
            city=dest,
        )

    # ── 2. Fetch weather ──
    weather_report: WeatherReport = tool(
        "researcher", "get_weather",
        destination=dest,
        start_date=start,
        end_date=end,
    )

    # ── 3. Search POIs ──
    prefs = intent.preferences
    cat_list = list(prefs.interests) if prefs and prefs.interests else None

    pois = tool(
        "researcher", "search_places",
        destination=dest,
        categories=cat_list,
    )

    poi_result = POISearchResult(
        all_pois=pois,
        source="mock-lbs-service",
        searched_categories=[c.value for c in cat_list] if cat_list else ["all"],
    )

    # ── 4. Transportation (optional context) ──
    transport = TransportationReport(source="mock-routing-service")

    # ── 5. RAG knowledge retrieval ──
    rag_results = _get_rag().query_destination(dest, k=3)
    tools_called = ["get_weather", "search_places"]
    rag_text = ""
    if rag_results:
        tools_called.append("rag_retriever")
        rag_text = _format_rag_results(rag_results)

    # ── Assemble report ──
    report = ResearchReport(
        destination_info=geo,
        weather=weather_report,
        pois=poi_result,
        transportation=transport,
        metadata=ResearchMetadata(tools_called=tools_called),
    )

    # Attach warnings (including knowledge from RAG)
    warnings = []
    if not pois:
        warnings.append(f"在{dest}未找到相关兴趣点")
    if not weather_report.forecasts:
        warnings.append(f"无法获取{dest}的天气信息")

    # Add RAG knowledge as informational warnings (prefixed with 💡)
    if rag_text:
        report.weather.overall_summary += f"\n\n{rag_text}"
        for r in rag_results:
            section = r.get("section", "")
            text_preview = r["text"][:80].replace("\n", " ")
            warnings.append(f"💡 {section}: {text_preview}…")

    report.warnings = warnings

    return {
        "travel_intent": intent,
        "research_report": report,
        "warnings": state.get("warnings", []) + warnings,
        "current_phase": "analyze",
    }


def _format_rag_results(results: list[dict]) -> str:
    """Format RAG knowledge chunks into a readable text block."""
    sections = []
    for r in results:
        text = r.get("text", "")
        section = r.get("section", "")
        lines = text.split("\n")
        body = "\n".join(lines[1:]) if len(lines) > 1 else text
        sections.append(f"📖 {section}\n{body.strip()[:300]}")
    return "\n\n".join(sections)
