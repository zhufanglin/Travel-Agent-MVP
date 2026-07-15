# Backend-Frontend Contract — AI Travel Agent

## Overview

The frontend (Streamlit, built by Trae) communicates with the backend
through a single interface module:

```
from travel_agent.services.agent_interface import run_agent, run_agent_stream
```

No direct imports from agents, graph, or tools modules are needed.

---

## 1. GraphState Fields (Internal State)

The backend uses a `GraphState` (TypedDict) that flows through all agents.
Frontend receives a serialized (dict) version of the final state.

| Field | Type | Produced By | Description |
|-------|------|-------------|-------------|
| `user_input` | `str` | User | Raw text input |
| `travel_intent` | `TravelIntent \| None` | Coordinator | Parsed travel intent |
| `research_report` | `ResearchReport \| None` | Researcher | Weather, POIs, routes |
| `analysis_result` | `AnalysisResult \| None` | Analyst | Scored recommendations |
| `travel_plan` | `TravelPlan \| None` | Planner | Final day-by-day itinerary |
| `current_phase` | `str` | All agents | `parse` → `research` → `analyze` → `plan` → `complete` |
| `errors` | `list[str]` | All agents | Fatal errors |
| `warnings` | `list[str]` | All agents | Non-fatal warnings |
| `missing_info` | `list[str]` | Coordinator | Fields needing clarification |

---

## 2. Agent Pipeline

```
User Input
    │
    ▼
┌──────────────────┐
│  Coordinator     │  Reads: user_input
│  (parse)         │  Produces: travel_intent
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Researcher      │  Reads: travel_intent
│  (research)      │  Produces: research_report
│                  │  Calls tools: get_weather, search_places
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Analyst         │  Reads: travel_intent, research_report
│  (analyze)       │  Produces: analysis_result
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Planner         │  Reads: travel_intent, analysis_result
│  (plan)          │  Produces: travel_plan
│                  │  Calls tools: estimate_budget
└──────┬───────────┘
       │
       ▼
  Complete State
```

---

## 3. Frontend Interface Functions

### 3.1 `run_agent(user_input: str) -> dict`

Synchronous call — returns complete result after all agents finish.

```python
from travel_agent.services.agent_interface import run_agent

result = run_agent("我想去北京玩3天，预算3000")

# Result structure:
{
    "travel_intent": { ... } | None,      # Serialized TravelIntent
    "research_report": { ... } | None,    # Serialized ResearchReport
    "analysis_result": { ... } | None,    # Serialized AnalysisResult
    "travel_plan": { ... } | None,        # Serialized TravelPlan
    "current_phase": "complete",          # or "error"
    "tool_trace": [ ... ],                # List of tool call records
    "warnings": [ "..." ],                # Non-fatal warnings
    "errors": [ "..." ],                  # Only present on failure
}
```

### 3.2 `run_agent_stream(user_input: str) -> Generator[dict]`

Streaming interface — yields progress updates for real-time UI.

```python
from travel_agent.services.agent_interface import run_agent_stream

for step in run_agent_stream("我想去北京"):
    phase = step.get("current_phase")     # "parse" | "research" | "analyze" | "plan" | "complete"
    updated = step.get("updated_fields")   # Newly populated fields dict
    progress = f"{step.get('completed_steps')}/{step.get('total_steps')}"
    # Update UI with step info
```

Stream yields:
```python
# Step 1:
{"current_phase": "research", "updated_fields": {"travel_intent": {...}}, "completed_steps": 1, "total_steps": 4}

# Step 2:
{"current_phase": "analyze", "updated_fields": {"research_report": {...}}, "completed_steps": 2, "total_steps": 4}

# Step 3:
{"current_phase": "plan", "updated_fields": {"analysis_result": {...}}, "completed_steps": 3, "total_steps": 4}

# Step 4:
{"current_phase": "complete", "updated_fields": {"travel_plan": {...}}, "completed_steps": 4, "total_steps": 4}

# Final:
{"tool_trace": [...]}
```

---

## 4. Schema Structures (Serialized as dicts)

### TravelIntent (from coordinator)

```json
{
    "destination": "北京",
    "origin": null,
    "start_date": "2026-07-20",
    "end_date": null,
    "duration_days": 3,
    "companions": 2,
    "companion_info": "和朋友",
    "budget": {"min_amount": 0, "max_amount": 3000, "currency": "CNY", "level": null},
    "preferences": {
        "interests": ["attraction", "restaurant"],
        "cuisine_preferences": [],
        "pace": "moderate",
        "accommodation_type": "hotel",
        "special_requirements": []
    },
    "constraints": {
        "max_budget": null,
        "budget_level": null,
        "must_visit": [],
        "avoid_places": [],
        "transportation_mode": null,
        "dietary_restrictions": [],
        "mobility_concerns": false
    },
    "purpose": "leisure",
    "raw_input": "我想去北京玩3天"
}
```

### ResearchReport (from researcher)

```json
{
    "destination_info": {
        "name": "北京",
        "address": "北京市",
        "coordinate": {"lat": 39.9042, "lng": 116.4074},
        "city": "北京",
        "district": "",
        "formatted": ""
    },
    "weather": {
        "forecasts": [
            {
                "forecast_date": "2026-07-20",
                "condition": "sunny",
                "temperature_high": 35.0,
                "temperature_low": 28.0,
                "humidity": 60,
                "precipitation_probability": 10,
                "description": "晴空万里，阳光充足"
            }
        ],
        "overall_summary": "北京2026-07-20至2026-07-22天气预报：以晴为主...",
        "source": "mock-weather-service"
    },
    "pois": {
        "all_pois": [
            {
                "name": "故宫博物院",
                "category": "attraction",
                "subcategory": "历史博物馆",
                "location": {"name": "故宫博物院", "address": "...", "coordinate": {"lat": 39.9163, "lng": 116.3972}},
                "rating": 4.8,
                "avg_cost": 60.0,
                "opening_hours": "08:30-17:00 (周一闭馆)",
                "tags": ["历史文化", "世界遗产"]
            }
        ],
        "source": "mock-lbs-service"
    },
    "warnings": []
}
```

### AnalysisResult (from analyst)

```json
{
    "summary": "根据你的偏好，从8个地点中筛选出8个推荐...",
    "recommended_pois": [
        {
            "poi": { "...": "..." },
            "score": 9.5,
            "match_reasons": ["评分高 (4.8)", "符合兴趣: 景点"],
            "concerns": [],
            "suggested_visit_duration": null,
            "recommended_meal": null
        }
    ],
    "daily_clusters": [
        {
            "day_index": 0,
            "label": "第1天: 北京经典探索",
            "pois": [ "...scored POIs..." ],
            "area": "",
            "notes": []
        }
    ],
    "top_attractions": [ "...scored POIs..." ],
    "top_restaurants": [ "...scored POIs..." ],
    "reasoning_details": ["基于景点偏好筛选"],
    "warnings": []
}
```

### TravelPlan (from planner) — FINAL OUTPUT

```json
{
    "title": "北京3日游",
    "destination": "北京",
    "days": [
        {
            "day_index": 0,
            "title": "第1天: 北京经典探索",
            "date": "2026-07-20",
            "activities": [
                {
                    "name": "故宫博物院",
                    "description": "探索故宫博物院",
                    "location": { "name": "故宫博物院", ... },
                    "category": "attraction",
                    "time_slot": { "start_time": "09:00", "end_time": "12:00", "label": "上午" },
                    "estimated_cost": 60.0,
                    "notes": [],
                    "tags": ["历史文化", "世界遗产"]
                }
            ],
            "meals": [
                { "meal_type": "lunch", "suggestion": "在附近餐厅解决午餐", "estimated_cost": 60 },
                { "meal_type": "dinner", "suggestion": "品尝当地特色美食", "estimated_cost": 80 }
            ],
            "transport_between_activities": [],
            "daily_budget_estimate": 500,
            "tips": ["建议查看当日天气预报，合理安排出行"]
        }
    ],
    "budget_breakdown": {
        "total_estimated": 3000,
        "accommodation_total": 840,
        "food_total": 720,
        "transportation_total": 500,
        "activities_total": 480,
        "miscellaneous_total": 240,
        "currency": "CNY"
    },
    "overview": "3天北京之旅，适合2人出行...",
    "notes": [
        "建议提前预订酒店和热门景点门票",
        "出行前查看当地天气，准备合适衣物",
        "下载当地地图App方便导航"
    ],
    "packing_tips": ["身份证/护照", "手机充电器/移动电源", "常用药品"]
}
```

---

## 5. Tool Trace Format

Every tool call is recorded for frontend display.

```json
[
    {
        "agent": "researcher",
        "tool_name": "get_weather",
        "input": "{'destination': '北京', 'start_date': '2026-07-20', 'end_date': '2026-07-22'}",
        "output": "forecasts=[DayForecast(...)] overall_summary='...'",
        "status": "success",
        "duration_ms": 12.5
    },
    {
        "agent": "researcher",
        "tool_name": "search_places",
        "input": "{'destination': '北京', 'categories': ['attraction', 'restaurant']}",
        "output": "[POI(name='故宫博物院'), POI(name='八达岭长城'), ...]",
        "status": "success",
        "duration_ms": 8.3
    }
]
```

Frontend rendering:
- Show `agent` icon + `tool_name`
- `status` → green check / red x
- `duration_ms` → timing badge
- Expandable detail for `input` / `output`

---

## 6. Streamlit Display Mapping

| Frontend Section | Backend Field | Notes |
|-----------------|---------------|-------|
| **Phase indicator** (4 steps) | `current_phase` | Show 4 icons, light up current |
| **Intent summary** | `travel_intent` | Show destination, dates, budget |
| **Weather widget** | `research_report.weather` | Per-day cards with emoji |
| **POI browser** | `research_report.pois` | Filterable by category |
| **Recommendations** | `analysis_result.recommended_pois` | Sorted by score |
| **Daily itinerary** | `travel_plan.days` | Timeline per day |
| **Budget breakdown** | `travel_plan.budget_breakdown` | Pie chart or table |
| **Tool trace log** | `tool_trace` | Expandable JSON viewer |
| **Error banner** | `errors` | Red alert box |
| **Warning list** | `warnings` | Yellow info box |

---

## 7. Error Handling

```python
# Backend error states:
current_phase = "error"  # Pipeline halted
errors = [
    "Tool xxx failed: connection refused",
    "Analyst: no research_report in state",
]

# Frontend should:
# 1. Show a red error banner with the error messages
# 2. Show whatever partial data is available
# 3. Allow user to retry with modified input
```

---

## 8. File Structure (Backend)

```
src/travel_agent/
├── agents/
│   ├── __init__.py
│   ├── coordinator.py     # Node: parse intent
│   ├── researcher.py      # Node: gather data
│   ├── analyst.py          # Node: score & cluster
│   └── planner.py         # Node: build itinerary
├── graph/
│   ├── __init__.py
│   ├── state.py           # GraphState TypedDict
│   └── workflow.py        # LangGraph StateGraph
├── schemas/               # Pydantic models (already defined)
│   ├── common.py, travel.py, research.py, analysis.py, plan.py
├── services/
│   ├── __init__.py
│   ├── agent_interface.py # ← Frontend imports this
│   ├── llm_client.py      # LLM factory
│   └── runner.py          # run/stream workflow
├── tools/
│   ├── __init__.py
│   ├── weather.py, place_search.py, route.py, budget.py
│   └── registry.py        # Tool registry + trace
└── config.py
```
