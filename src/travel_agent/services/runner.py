"""Workflow runner — entry point for executing the travel agent pipeline.

Provides both synchronous and streaming interfaces for the LangGraph workflow.
The streaming interface supports real-time progress updates for Streamlit.
"""

from typing import AsyncGenerator, Generator, Optional

from travel_agent.graph.state import GraphState, create_initial_state
from travel_agent.graph.workflow import app, create_workflow
from travel_agent.schemas.travel import TravelIntent
from travel_agent.tools.registry import clear_trace, get_trace


def run_travel_agent(
    user_input: str,
    prebuilt_intent: Optional[TravelIntent] = None,
) -> GraphState:
    """Run the full travel agent pipeline synchronously.

    Args:
        user_input: Natural language travel request from the user.
        prebuilt_intent: Optional pre-built TravelIntent from form data.
            When provided, the coordinator skips LLM parsing and uses this.

    Returns:
        Complete GraphState with all agent outputs populated:
        - travel_intent
        - research_report
        - analysis_result
        - travel_plan
        - current_phase

    Raises:
        ValueError: If the pipeline fails to produce a travel plan.
    """
    clear_trace()

    initial = create_initial_state(user_input)
    if prebuilt_intent:
        initial["travel_intent"] = prebuilt_intent
    workflow = create_workflow()
    result: GraphState = workflow.invoke(initial)

    # If the workflow ended with errors, surface them
    errors = result.get("errors", [])
    if errors and not result.get("travel_plan"):
        raise ValueError(f"Workflow completed with errors: {'; '.join(errors)}")

    return result


def stream_travel_agent(
    user_input: str,
    prebuilt_intent: Optional[TravelIntent] = None,
) -> Generator[dict, None, None]:
    """Run the travel agent pipeline with streaming step updates.

    Yields a dict per step so the Streamlit frontend can show
    real-time progress of each agent.

    Args:
        user_input: Natural language travel request.
        prebuilt_intent: Optional pre-built TravelIntent from form data.

    Yields:
        Dicts with keys:
        - current_phase: which agent is running
        - updated_fields: dict of fields that were just populated
        - tool_trace: accumulated tool call log
    """
    clear_trace()

    initial = create_initial_state(user_input)
    if prebuilt_intent:
        initial["travel_intent"] = prebuilt_intent
    workflow = create_workflow()

    # Track what we've already sent
    seen_fields: set[str] = set()

    phase_map = {
        "parse": "parse",
        "research": "research",
        "analyze": "analyze",
        "plan": "plan",
    }

    for event in workflow.stream(initial):
        for node_name, node_output in event.items():
            if not isinstance(node_output, dict):
                continue

            # Use graph node name for phase, not the next-phase hint
            phase = phase_map.get(node_name, node_output.get("current_phase", node_name))
            updated = {}

            # Collect newly populated fields
            for field in ["travel_intent", "research_report", "analysis_result", "travel_plan"]:
                if field in node_output and field not in seen_fields:
                    val = node_output[field]
                    if val is not None:
                        updated[field] = val
                        seen_fields.add(field)

            yield {
                "current_phase": phase,
                "updated_fields": updated,
                "total_steps": 4,
                "completed_steps": len(seen_fields),
            }

    yield {
        "current_phase": "complete",
        "updated_fields": {},
        "tool_trace": get_trace(),
        "total_steps": 4,
        "completed_steps": 4,
    }


async def stream_travel_agent_async(
    user_input: str,
    prebuilt_intent: Optional[TravelIntent] = None,
) -> AsyncGenerator[dict, None]:
    """Async version of stream_travel_agent for async frameworks."""
    for step in stream_travel_agent(user_input, prebuilt_intent):
        yield step
