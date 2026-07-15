import streamlit as st


PHASE_ORDER = ["idle", "parse", "research", "analyze", "plan", "complete"]

AGENT_LIST = ["coordinator", "researcher", "analyst", "planner"]

# Map agent -> phase that produces its output
AGENT_PHASE_MAP = {
    "coordinator": "parse",
    "researcher": "research",
    "analyst": "analyze",
    "planner": "plan",
}

# Map agent -> its output field in graph_state
AGENT_OUTPUT_FIELD = {
    "coordinator": "travel_intent",
    "researcher": "research_report",
    "analyst": "analysis_result",
    "planner": "travel_plan",
}


def init_session_state():
    if "graph_state" not in st.session_state:
        st.session_state.graph_state = {
            "current_phase": "idle",
            "travel_intent": None,
            "research_report": None,
            "analysis_result": None,
            "travel_plan": None,
            "tool_trace": [],
            "errors": [],
        }
    if "ui_state" not in st.session_state:
        st.session_state.ui_state = {
            "active_tab": "map",
            "tool_trace_expanded": True,
            "selected_day": 0,
        }


def get_agent_status(agent_name: str) -> dict:
    gs = st.session_state.graph_state
    phase = gs["current_phase"]
    phase_idx = PHASE_ORDER.index(phase) if phase in PHASE_ORDER else 0

    agent_phase = AGENT_PHASE_MAP.get(agent_name, "")
    agent_phase_idx = PHASE_ORDER.index(agent_phase) if agent_phase in PHASE_ORDER else -1

    output_field = AGENT_OUTPUT_FIELD.get(agent_name, "")
    has_output = gs.get(output_field) is not None
    has_error = bool(gs.get("errors"))

    if has_error:
        return {"status": "error", "label": "失败", "icon": "❌", "color": "#ef4444"}

    if has_output:
        return {"status": "completed", "label": "完成", "icon": "✅", "color": "#22c55e"}

    if phase_idx > agent_phase_idx:
        return {"status": "completed", "label": "完成", "icon": "✅", "color": "#22c55e"}

    if phase == agent_phase:
        return {"status": "running", "label": "执行中", "icon": "⏳", "color": "#3b82f6"}

    if phase == "idle":
        return {"status": "idle", "label": "就绪", "icon": "⚪", "color": "#52525b"}

    return {"status": "pending", "label": "等待中", "icon": "⏸️", "color": "#52525b"}


def get_agent_output_summary(agent_name: str) -> str | None:
    gs = st.session_state.graph_state
    output_field = AGENT_OUTPUT_FIELD.get(agent_name, "")
    val = gs.get(output_field)
    if val is None:
        return None
    for attr in ("display_summary", "summary", "display"):
        if hasattr(val, attr):
            return getattr(val, attr)
    return str(val)[:100]
