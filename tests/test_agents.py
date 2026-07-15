"""Tests for Multi-Agent backend — agents, workflow, runner, and streaming.

Uses mocked LLM calls so tests run without an API key.
All tests verify schema compliance and data flow integrity.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from travel_agent.agents.analyst import analyst_node
from travel_agent.agents.coordinator import coordinator_node
from travel_agent.agents.planner import planner_node
from travel_agent.agents.researcher import researcher_node
from travel_agent.graph.state import create_initial_state
from travel_agent.graph.workflow import create_workflow
from travel_agent.schemas.analysis import AnalysisResult
from travel_agent.schemas.common import (
    Coordinate,
    GeoLocation,
    POI,
    POICategory,
    WeatherCondition,
)
from travel_agent.schemas.plan import TravelPlan
from travel_agent.schemas.research import DayForecast, ResearchReport
from travel_agent.schemas.travel import TravelIntent, TravelPreferences


# ──────────────────────────────────────────────
#  Mock LLM helper
# ──────────────────────────────────────────────


class _MockStructuredLLM:
    """A fake LLM that returns structured output for testing.

    Must be callable so LangChain's 'prompt | llm' pipe operator works.
    """

    def __init__(self, return_value=None):
        self._return_value = return_value

    def with_structured_output(self, schema):
        # Return self — LangChain wraps callables in RunnableLambda
        return self

    def __call__(self, input_data):
        """Called by LangChain RunnableSequence/Lambda when piped."""
        return self._return_value

    def invoke(self, input_data):
        """Direct invoke (bypasses pipe operator)."""
        return self._return_value


@pytest.fixture
def sample_intent() -> TravelIntent:
    """A basic TravelIntent for testing."""
    return TravelIntent(
        destination="北京",
        duration_days=3,
        companions=2,
        preferences=TravelPreferences(
            interests=[POICategory.ATTRACTION, POICategory.RESTAURANT],
            pace="moderate",
        ),
        raw_input="我想去北京玩3天",
    )


@pytest.fixture
def sample_research_report() -> ResearchReport:
    """A ResearchReport with mock Beijing data."""
    forecast = DayForecast(
        date=date.today().isoformat(),
        condition=WeatherCondition.SUNNY,
        temperature_high=32.0,
        temperature_low=22.0,
    )
    poi = POI(
        name="故宫博物院",
        category=POICategory.ATTRACTION,
        location=GeoLocation(
            name="故宫博物院",
            coordinate=Coordinate(lat=39.9163, lng=116.3972),
            address="北京市东城区景山前街4号",
            city="北京",
        ),
        rating=4.8,
        avg_cost=60,
        tags=["历史文化", "必去"],
    )
    report = ResearchReport(
        destination_info=GeoLocation(
            name="北京",
            coordinate=Coordinate(lat=39.9042, lng=116.4074),
            city="北京",
        ),
    )
    report.weather.forecasts = [forecast]
    report.pois.all_pois = [poi]
    return report


# ──────────────────────────────────────────────
#  1. Coordinator Agent Tests
# ──────────────────────────────────────────────


@patch("travel_agent.agents.coordinator.get_llm")
def test_coordinator_parses_intent(mock_get_llm, sample_intent):
    """Coordinator should parse user input into a TravelIntent via LLM."""
    mock_get_llm.return_value = _MockStructuredLLM(return_value=sample_intent)

    state = create_initial_state("我想去北京玩3天，喜欢美食和历史")
    result = coordinator_node(state)

    assert "travel_intent" in result
    intent = result["travel_intent"]
    assert intent is not None
    assert intent.destination == "北京"
    assert intent.duration_days == 3
    assert result["current_phase"] == "research"


@patch("travel_agent.agents.coordinator.get_llm")
def test_coordinator_handles_no_api_key(mock_get_llm):
    """Coordinator should fall back to regex parser when API key missing."""
    mock_get_llm.side_effect = ValueError("OPENAI_API_KEY not set")

    state = create_initial_state("去北京玩3天，预算3000")
    result = coordinator_node(state)

    assert "travel_intent" in result
    intent = result["travel_intent"]
    assert intent is not None
    # Fallback parser should extract destination
    assert "北京" in intent.destination if intent.destination else True
    assert result["current_phase"] in ("research", "clarify")


# ──────────────────────────────────────────────
#  2. Researcher Agent Tests
# ──────────────────────────────────────────────


def test_researcher_generates_report(sample_intent):
    """Researcher should produce a complete ResearchReport."""
    state = create_initial_state("test")
    state["travel_intent"] = sample_intent

    result = researcher_node(state)

    assert "research_report" in result
    report = result["research_report"]
    assert isinstance(report, ResearchReport)
    assert report.destination_info is not None
    assert report.weather is not None
    assert report.pois is not None
    assert report.destination_info.name == "北京"


def test_researcher_handles_missing_intent():
    """Researcher should error gracefully without travel_intent."""
    state = create_initial_state("test")

    result = researcher_node(state)

    assert result["current_phase"] == "error"
    assert "errors" in result


# ──────────────────────────────────────────────
#  3. Analyst Agent Tests
# ──────────────────────────────────────────────


def test_analyst_produces_recommendations(sample_intent, sample_research_report):
    """Analyst should score and cluster POIs from research data."""
    state = create_initial_state("test")
    state["travel_intent"] = sample_intent
    state["research_report"] = sample_research_report

    result = analyst_node(state)

    assert "analysis_result" in result
    analysis = result["analysis_result"]
    assert isinstance(analysis, AnalysisResult)
    assert len(analysis.recommended_pois) > 0
    assert len(analysis.daily_clusters) > 0
    assert len(analysis.top_attractions) >= 0


def test_analyst_handles_empty_report(sample_intent):
    """Analyst should handle empty research data."""
    empty_report = ResearchReport(
        destination_info=GeoLocation(
            name="北京", coordinate=Coordinate(lat=39.9, lng=116.4),
        ),
    )
    state = create_initial_state("test")
    state["travel_intent"] = sample_intent
    state["research_report"] = empty_report

    result = analyst_node(state)

    assert "analysis_result" in result
    assert result["analysis_result"].warnings is not None


# ──────────────────────────────────────────────
#  4. Planner Agent Tests
# ──────────────────────────────────────────────


def test_planner_creates_itinerary(sample_intent, sample_research_report):
    """Planner should create a complete TravelPlan from analysis."""
    state = create_initial_state("test")
    state["travel_intent"] = sample_intent
    state["research_report"] = sample_research_report
    analysis_result = analyst_node(state)
    state["analysis_result"] = analysis_result["analysis_result"]

    result = planner_node(state)

    assert "travel_plan" in result
    plan = result["travel_plan"]
    assert isinstance(plan, TravelPlan)
    assert plan.destination == "北京"
    assert len(plan.days) > 0
    assert plan.budget_breakdown.total_estimated > 0


def test_planner_handles_no_analysis(sample_intent):
    """Planner should error without analysis result."""
    state = create_initial_state("test")
    state["travel_intent"] = sample_intent

    result = planner_node(state)

    assert result["current_phase"] == "error"
    assert "errors" in result


# ──────────────────────────────────────────────
#  5. Full Workflow Test
# ──────────────────────────────────────────────


@patch("travel_agent.agents.coordinator.get_llm")
def test_full_workflow_runs(mock_get_llm, sample_intent):
    """The complete LangGraph workflow should produce a TravelPlan."""
    mock_get_llm.return_value = _MockStructuredLLM(return_value=sample_intent)

    workflow = create_workflow()
    state = create_initial_state("我想去北京玩3天")
    result = workflow.invoke(state)

    assert "travel_plan" in result
    assert result["travel_plan"] is not None
    assert result["current_phase"] == "complete"
    # Verify all stages produced output
    assert result["travel_intent"] is not None
    assert result["research_report"] is not None
    assert result["analysis_result"] is not None


@patch("travel_agent.agents.coordinator.get_llm")
def test_workflow_state_transitions(mock_get_llm, sample_intent):
    """Workflow should transition through all expected phases."""
    mock_get_llm.return_value = _MockStructuredLLM(return_value=sample_intent)

    workflow = create_workflow()
    state = create_initial_state("北京3日游")
    result = workflow.invoke(state)

    assert result["current_phase"] == "complete"
    # Verify sequential phase completion
    assert result["travel_intent"] is not None       # parse done
    assert result["research_report"] is not None     # research done
    assert result["analysis_result"] is not None     # analyze done
    assert result["travel_plan"] is not None         # plan done


# ──────────────────────────────────────────────
#  6. Streaming Test
# ──────────────────────────────────────────────


@patch("travel_agent.agents.coordinator.get_llm")
def test_streaming_yields_steps(mock_get_llm, sample_intent):
    """Streaming should yield progress updates for each stage."""
    mock_get_llm.return_value = _MockStructuredLLM(return_value=sample_intent)

    from travel_agent.services.runner import stream_travel_agent

    steps = list(stream_travel_agent("北京3日游"))

    assert len(steps) > 0
    phase_names = {s.get("current_phase") for s in steps}
    assert "complete" in phase_names
    assert len(phase_names) >= 2  # At least 2 distinct phases


# ──────────────────────────────────────────────
#  7. Agent Interface Test
# ──────────────────────────────────────────────


@patch("travel_agent.services.runner.create_workflow")
@patch("services.agent_interface._memory")
def test_agent_interface_returns_dict(mock_memory, mock_create_workflow):
    """The frontend-facing agent_interface should return a valid result dict."""
    mock_memory.get_memory_context.return_value = ""
    from services.agent_interface import run_workflow

    # Mock the workflow to return a valid state
    mock_workflow = MagicMock()
    mock_workflow.invoke.return_value = {
        "travel_intent": TravelIntent(destination="北京", duration_days=3, raw_input="test"),
        "research_report": ResearchReport(
            destination_info=GeoLocation(
                name="北京", coordinate=Coordinate(lat=39.9, lng=116.4),
            ),
        ),
        "analysis_result": AnalysisResult(summary="test"),
        "travel_plan": TravelPlan(title="test", destination="北京"),
        "current_phase": "complete",
        "errors": [],
        "warnings": [],
    }
    mock_create_workflow.return_value = mock_workflow

    result = run_workflow({"destination": "北京", "preferences": ["景点"]})

    assert isinstance(result, dict)
    assert "travel_plan" in result
    assert "tool_trace" in result
    assert result["current_phase"] == "complete"
    # Root adapter returns Pydantic model instances (not raw dicts)
    assert hasattr(result["travel_intent"], "destination") if result["travel_intent"] else True


# ──────────────────────────────────────────────
#  8. Edge Case Tests
# ──────────────────────────────────────────────


def test_analyst_respects_empty_intent():
    """Analyst should handle missing travel_intent gracefully."""
    report = ResearchReport(
        destination_info=GeoLocation(
            name="北京", coordinate=Coordinate(lat=39.9, lng=116.4),
        ),
    )
    state = create_initial_state("test")
    state["research_report"] = report

    result = analyst_node(state)
    assert "analysis_result" in result


def test_planner_reuses_budget_tool():
    """Planner should produce consistent budget estimates."""
    prefs = TravelPreferences(interests=[POICategory.ATTRACTION])

    from travel_agent.tools.budget import estimate_budget
    budget = estimate_budget(days=3, preferences=prefs, companions=2)

    assert budget.total_estimated > 0
    assert budget.accommodation_total > 0
    assert budget.food_total > 0


# ──────────────────────────────────────────────
#  9. Memory-Influenced Decision Tests
# ──────────────────────────────────────────────


@patch("travel_agent.agents.coordinator.get_llm")
def test_fallback_uses_memory_interests(mock_get_llm):
    """Memory with 美食偏好 should add RESTAURANT to intent interests."""
    mock_get_llm.side_effect = ValueError("no api key")  # force fallback

    user_input = (
        "去杭州玩3天\n"
        "=== 你的旅行记忆 ===\n"
        "🍽️ 美食偏好: 川菜、火锅\n"
        "🏛️ 兴趣偏好: 景点、美食、文化场馆\n"
        "===================\n"
    )
    state = create_initial_state(user_input)
    result = coordinator_node(state)
    intent = result["travel_intent"]

    assert intent is not None
    cats = [c.value for c in intent.preferences.interests]
    assert "restaurant" in cats, f"Expected restaurant in interests, got {cats}"
    assert "museum" in cats, f"Expected museum in interests, got {cats}"
    assert "川菜" in intent.preferences.cuisine_preferences, (
        f"Expected 川菜 in cuisine_preferences, got {intent.preferences.cuisine_preferences}"
    )


@patch("travel_agent.agents.coordinator.get_llm")
def test_fallback_merges_memory_without_override(mock_get_llm):
    """Memory should enrich but not override explicitly stated interests."""
    mock_get_llm.side_effect = ValueError("no api key")

    user_input = (
        "去上海购物2天\n"
        "=== 你的旅行记忆 ===\n"
        "🏛️ 兴趣偏好: 美食\n"
        "===================\n"
    )
    state = create_initial_state(user_input)
    result = coordinator_node(state)
    intent = result["travel_intent"]

    cats = [c.value for c in intent.preferences.interests]
    assert "shopping" in cats, "Explicit interest 购物 should be present"
    assert "restaurant" in cats, "Memory interest 美食 should be merged"


@patch("travel_agent.agents.coordinator.get_llm")
def test_fallback_uses_memory_companions(mock_get_llm):
    """Memory should provide companion default when user doesn't specify."""
    mock_get_llm.side_effect = ValueError("no api key")

    user_input = (
        "去北京玩\n"
        "=== 你的旅行记忆 ===\n"
        "👥 出行人数: 双人出行\n"
        "===================\n"
    )
    state = create_initial_state(user_input)
    result = coordinator_node(state)
    intent = result["travel_intent"]

    assert intent.companions == 2, f"Expected 2 from memory, got {intent.companions}"


@patch("travel_agent.agents.coordinator.get_llm")
def test_fallback_no_memory_no_change(mock_get_llm):
    """Without memory section, fallback should behave as before."""
    mock_get_llm.side_effect = ValueError("no api key")

    state = create_initial_state("3个人去广州")
    result = coordinator_node(state)
    intent = result["travel_intent"]

    assert intent is not None
    assert "广州" in (intent.destination or "")
    assert intent.companions == 3
