"""Tool registry — central registry for all agent-callable tools.

Provides a unified interface for agents to discover and invoke tools,
and supports tool-call tracing for the Streamlit frontend.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from travel_agent.tools.budget import estimate_budget
from travel_agent.tools.place_search import search_places
from travel_agent.tools.route import calculate_route
from travel_agent.tools.weather import get_weather

# ── Tool definition ──

ToolFunc = Callable[..., Any]


class ToolDefinition:
    """Metadata for a registered tool."""

    def __init__(self, name: str, description: str, fn: ToolFunc):
        self.name = name
        self.description = description
        self.fn = fn


# ── Trace entry ──


class ToolTraceEntry:
    """Record of a single tool invocation for frontend display."""

    def __init__(self, agent: str, tool_name: str, tool_input: Any, tool_output: Any, status: str, duration_ms: float):
        self.agent = agent
        self.tool_name = tool_name
        self.input = str(tool_input)[:200]
        self.output = str(tool_output)[:200]
        self.status = status
        self.duration_ms = round(duration_ms, 1)

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "tool_name": self.tool_name,
            "input": self.input,
            "output": self.output,
            "status": self.status,
            "duration_ms": self.duration_ms,
        }


# ── Registry ──

_tools: dict[str, ToolDefinition] = {}
_trace: list[ToolTraceEntry] = []


def register_tool(name: str, description: str, fn: ToolFunc) -> None:
    """Register a tool so agents can discover it."""
    _tools[name] = ToolDefinition(name=name, description=description, fn=fn)


def get_tool(name: str) -> ToolDefinition:
    """Get a tool definition by name."""
    if name not in _tools:
        raise KeyError(f"Tool '{name}' not found in registry")
    return _tools[name]


def list_tools() -> list[dict]:
    """List all registered tools (for agent prompts)."""
    return [{"name": t.name, "description": t.description} for t in _tools.values()]


def call_tool(agent: str, tool_name: str, **kwargs) -> Any:
    """Invoke a tool with tracing.

    Args:
        agent: Name of the agent making the call.
        tool_name: Registered tool name.
        **kwargs: Arguments to pass to the tool function.

    Returns:
        The tool function's return value.
    """
    tool = get_tool(tool_name)
    start = time.time()
    try:
        result = tool.fn(**kwargs)
        elapsed = (time.time() - start) * 1000
        _trace.append(ToolTraceEntry(
            agent=agent, tool_name=tool_name,
            tool_input=kwargs, tool_output=result,
            status="success", duration_ms=elapsed,
        ))
        return result
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        _trace.append(ToolTraceEntry(
            agent=agent, tool_name=tool_name,
            tool_input=kwargs, tool_output=str(e),
            status="error", duration_ms=elapsed,
        ))
        raise


def get_trace() -> list[dict]:
    """Get all tool invocation traces for the current session."""
    return [t.to_dict() for t in _trace]


def clear_trace() -> None:
    """Clear the tool trace (call at start of each run)."""
    _trace.clear()


# ── Register built-in tools ──

register_tool("search_places", "搜索目的地的景点、餐厅、住宿等兴趣点", search_places)
register_tool("get_weather", "获取目的地天气预报", get_weather)
register_tool("calculate_route", "计算两点之间的交通路线", calculate_route)
register_tool("estimate_budget", "估算旅行预算", estimate_budget)
