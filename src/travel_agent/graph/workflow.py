"""LangGraph workflow definition — orchestrates the multi-agent pipeline.

Defines the StateGraph with four nodes (parse → research → analyze → plan)
and compiles it into a runnable application.
"""

from langgraph.graph import END, StateGraph

from travel_agent.agents.analyst import analyst_node
from travel_agent.agents.coordinator import coordinator_node
from travel_agent.agents.planner import planner_node
from travel_agent.agents.researcher import researcher_node
from travel_agent.graph.state import GraphState


def create_workflow() -> StateGraph:
    """Build and return the compiled travel-planning workflow.

    Graph structure:
        START → parse → research → analyze → plan → END

    Returns:
        A compiled LangGraph StateGraph application.
    """
    builder = StateGraph(GraphState)

    # ── Register nodes ──
    builder.add_node("parse", coordinator_node)
    builder.add_node("research", researcher_node)
    builder.add_node("analyze", analyst_node)
    builder.add_node("plan", planner_node)

    # ── Define edges ──
    builder.set_entry_point("parse")
    builder.add_edge("parse", "research")
    builder.add_edge("research", "analyze")
    builder.add_edge("analyze", "plan")
    builder.add_edge("plan", END)

    # ── Compile ──
    return builder.compile()


def create_conditional_workflow() -> StateGraph:
    """Advanced workflow with conditional routing based on current_phase.

    This version supports error handling and clarification loops.
    Use this in production; create_workflow() is for simple MVP testing.
    """
    builder = StateGraph(GraphState)

    # ── Register nodes ──
    builder.add_node("parse", coordinator_node)
    builder.add_node("research", researcher_node)
    builder.add_node("analyze", analyst_node)
    builder.add_node("plan", planner_node)

    # ── Entry point ──
    builder.set_entry_point("parse")

    # ── Conditional routing ──
    def route_from_parse(state: GraphState) -> str:
        """Route based on coordinator output."""
        phase = state.get("current_phase", "clarify")
        if phase == "clarify":
            # Need more info — for MVP, proceed with defaults
            return "research"
        return "research"

    def route_from_research(state: GraphState) -> str:
        """Route from research to next stage."""
        errors = state.get("errors", [])
        if len(errors) > 2:
            return END
        return "analyze"

    def route_from_analyze(state: GraphState) -> str:
        """Route from analysis to planning."""
        return "plan"

    def route_from_plan(state: GraphState) -> str:
        """Final output."""
        return END

    # ── Conditional edges ──
    builder.add_conditional_edges("parse", route_from_parse)
    builder.add_conditional_edges("research", route_from_research)
    builder.add_conditional_edges("analyze", route_from_analyze)
    builder.add_conditional_edges("plan", route_from_plan)

    return builder.compile()


# Default: pre-compiled simple workflow
app = create_workflow()
