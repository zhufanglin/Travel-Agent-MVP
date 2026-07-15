"""Adapter — bridges Streamlit Frontend ↔ LangGraph Backend.

Converts structured form data into natural language input for the
Coordinator Agent. The Coordinator (LLM or fallback) then produces
a TravelIntent — the adapter no longer constructs it.
"""

import sys
from pathlib import Path

# Ensure src/ is on sys.path so 'from travel_agent...' imports work
_src = Path(__file__).resolve().parent.parent / "src"
if _src.is_dir() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from travel_agent.services.runner import run_travel_agent, stream_travel_agent
from travel_agent.tools.registry import get_trace
from travel_agent.memory.memory_manager import MemoryManager

# ── Memory — persists across sessions via SQLite ──
_memory = MemoryManager()


def run_workflow(form_input: dict) -> dict:
    """Execute the multi-agent pipeline via the Coordinator Agent.

    Memory is retrieved before planning and injected into the
    Coordinator's context. After planning, preferences and travel
    history are saved automatically.

    Args:
        form_input: Dict with keys:
            destination, start_date, end_date, travelers,
            budget_min, budget_max, preferences (list[str]), notes

    Returns:
        Dict for st.session_state.graph_state.
    """
    try:
        # 1. Build user input from form
        user_input = _format_user_input(form_input)

        # 2. Retrieve memory context (empty string for new users)
        memory_context = _memory.get_memory_context()

        # 3. Inject memory after the current request so the
        #    fallback regex parser prioritises the new input
        enriched_input = user_input
        if memory_context:
            enriched_input = user_input + "\n" + memory_context

        # 4. Run the workflow
        state = run_travel_agent(enriched_input)

        # 5. Save learned preferences + travel history
        intent = state.get("travel_intent")
        plan = state.get("travel_plan")
        if intent and plan:
            _memory.save_from_result(intent, plan)

        result = dict(state)
        result["tool_trace"] = get_trace()
        _ensure_keys(result)

        return result

    except Exception as e:
        return _error_response(str(e))


def get_workflow_stream(form_input: dict):
    """Stream the multi-agent pipeline step by step.

    The same flow as run_workflow() but yields progress updates
    for real-time Streamlit display.
    """
    user_input = _format_user_input(form_input)
    yield from stream_travel_agent(user_input)


# ── Internal helpers ──


def _format_user_input(form: dict) -> str:
    """Build a natural-language travel request from structured form data.

    The output reads like a real user message so the Coordinator
    (LLM or fallback Parser) can parse it naturally.

    Example:
        "去杭州旅游5天，从2026-07-20到2026-07-24，2人，
         预算2000-5000元，喜欢景点、美食、文化"
    """
    dest = form.get("destination", "")
    start = form.get("start_date", "")
    end = form.get("end_date", "")
    travelers = form.get("travelers", 1)
    bmin = form.get("budget_min", 0)
    bmax = form.get("budget_max", 0)
    prefs = form.get("preferences", [])
    notes = form.get("notes", "")

    # Convert date objects to ISO strings
    if hasattr(start, "isoformat"):
        start = start.isoformat()
    if hasattr(end, "isoformat"):
        end = end.isoformat()

    # Compute duration from date range
    days_info = ""
    if start and end:
        from datetime import date
        try:
            sd = date.fromisoformat(str(start)[:10]) if isinstance(start, str) else start
            ed = date.fromisoformat(str(end)[:10]) if isinstance(end, str) else end
            days = (ed - sd).days
            days_info = f"旅游{days}天"
        except (ValueError, TypeError):
            days_info = ""

    parts = [f"去{dest}"]
    if days_info:
        parts.append(days_info)
    if start:
        parts.append(f"从{start}出发")
    if end:
        parts.append(f"到{end}")
    parts.append(f"{travelers}人")
    if float(bmin) > 0 or float(bmax) > 0:
        parts.append(f"预算{float(bmin):.0f}-{float(bmax):.0f}元")
    if prefs:
        parts.append("喜欢" + "、".join(prefs))
    if notes:
        parts.append(f"备注：{notes}")

    return "，".join(parts)


def _ensure_keys(result: dict) -> None:
    """Ensure all expected frontend keys exist in the result."""
    for key in ("travel_intent", "research_report", "analysis_result", "travel_plan"):
        if key not in result:
            result[key] = None
    if "current_phase" not in result:
        result["current_phase"] = "complete"
    if "tool_trace" not in result:
        result["tool_trace"] = []
    if "errors" not in result:
        result["errors"] = []
    if "warnings" not in result:
        result["warnings"] = []


def _error_response(msg: str) -> dict:
    """Build a standard error response dict."""
    return {
        "current_phase": "error",
        "travel_intent": None,
        "research_report": None,
        "analysis_result": None,
        "travel_plan": None,
        "tool_trace": get_trace(),
        "errors": [msg],
        "warnings": [],
    }
