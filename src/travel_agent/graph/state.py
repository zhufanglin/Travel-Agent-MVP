"""LangGraph workflow state definition.

GraphState is the single source of truth flowing through the
multi-agent pipeline. Every node (agent) reads from and writes to
this state. The state is a TypedDict with Pydantic models as values,
enabling type-safe field access and LangGraph's reducer-based merging.
"""

from __future__ import annotations

from operator import add
from typing import Annotated, Optional

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import TypedDict

from travel_agent.schemas.analysis import AnalysisResult
from travel_agent.schemas.plan import TravelPlan
from travel_agent.schemas.research import ResearchReport
from travel_agent.schemas.travel import TravelIntent


class GraphState(TypedDict):
    """Workflow state — flows through all nodes in the LangGraph pipeline.

    Each field becomes available after its producing node completes.
    Optional fields are None until that stage runs.

    Streamlit reads from this state at the end of the workflow to render
    the final travel plan and intermediate results for transparency.
    """

    # ── Input layer ──
    user_input: str
    """Raw text input from the user via Streamlit."""

    messages: Annotated[list[AnyMessage], add_messages]
    """Conversation message history, auto-accumulated by LangGraph reducer."""

    # ── Intent parsing ──
    travel_intent: Optional[TravelIntent]
    """Structured travel intent parsed by Coordinator Agent.
    Produced by: Coordinator.parse_intent()"""

    missing_info: list[str]
    """Fields that need user clarification before proceeding.
    Produced by: Coordinator.parse_intent() or coordinator.review()"""

    # ── Research phase ──
    research_report: Optional[ResearchReport]
    """Factual data gathered by Researcher Agent via external tools.
    Produced by: Researcher.gather_info()"""

    # ── Analysis phase ──
    analysis_result: Optional[AnalysisResult]
    """Filtered, scored recommendations from Analyst Agent.
    Produced by: Analyst.analyze()"""

    # ── Planning phase ──
    travel_plan: Optional[TravelPlan]
    """Final day-by-day itinerary from Planner Agent.
    Produced by: Planner.create_plan()"""

    # ── Workflow control ──
    current_phase: str
    """Identifies the current stage in the workflow.
    Values: 'parse' | 'clarify' | 'research' | 'analyze' | 'plan' | 'review' | 'complete'"""

    errors: list[str]
    """Errors encountered during workflow execution.
    Used for graceful degradation — single tool failure shouldn't crash the pipeline."""

    warnings: list[str]
    """Non-fatal warnings accumulated across all stages."""

    max_iterations: int
    """Safety limit on workflow loops (e.g. research retry, clarification cycles)."""


def create_initial_state(user_input: str) -> GraphState:
    """Factory to create a fresh GraphState with sensible defaults.

    Args:
        user_input: Raw text from the user describing their trip.

    Returns:
        A new GraphState ready for the workflow.
    """
    return {
        "user_input": user_input,
        "messages": [],
        "travel_intent": None,
        "missing_info": [],
        "research_report": None,
        "analysis_result": None,
        "travel_plan": None,
        "current_phase": "parse",
        "errors": [],
        "warnings": [],
        "max_iterations": 5,
    }


def is_workflow_complete(state: GraphState) -> bool:
    """Check whether the workflow has reached a terminal state."""
    return state.get("current_phase") == "complete"


def has_fatal_errors(state: GraphState) -> bool:
    """Check whether the workflow should halt due to errors."""
    return len(state.get("errors", [])) >= 3
