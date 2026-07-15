"""Input section with real-time Agent streaming visualization.

When the user clicks "开始规划", the workflow runs via get_workflow_stream()
and each Agent's progress is shown live using st.status() before results render.
"""

import streamlit as st

from services.agent_interface import get_workflow_stream, run_workflow

# ── Agent display configuration ──
AGENT_STEPS = [
    {"phase": "parse",    "icon": "🧠", "label": "Coordinator Agent",  "desc": "解析旅行需求...",       "done": "旅行需求解析完成"},
    {"phase": "research", "icon": "🔍", "label": "Researcher Agent",   "desc": "采集天气和地点数据...", "done": "信息采集完成"},
    {"phase": "analyze",  "icon": "📊", "label": "Analyst Agent",      "desc": "评分筛选推荐地点...",   "done": "分析推荐完成"},
    {"phase": "plan",     "icon": "📋", "label": "Planner Agent",      "desc": "编排行程和预算...",     "done": "行程编排完成"},
]


def render_input_section():
    """Render the input form and handle streaming workflow execution."""
    gs = st.session_state.graph_state
    phase = gs.get("current_phase", "idle")

    # ── Streaming update: advance one step per rerun ──
    if phase not in ("idle", "complete", "error") and "stream_gen" in st.session_state:
        _advance_stream()
        _render_streaming_status()
        # Always rerun — either for next step or to transition to results
        st.rerun()
        return

    # ── Show form/results (no rerun needed, previous step handled it) ──
    if phase == "complete":
        return

    # ── Form UI (only shown when idle or errored) ──
    st.subheader("✈️ 旅行需求输入")

    if phase == "error":
        st.error("上轮规划执行出错，请调整输入后重试")

    _render_form()


# ── Streaming engine ──


def _advance_stream():
    """Advance the workflow generator by one step and update session state."""
    gen = st.session_state.get("stream_gen")
    if gen is None:
        st.session_state.streaming = False
        return

    try:
        step = next(gen)
    except StopIteration:
        st.session_state.streaming = False
        st.session_state.stream_gen = None
        return

    phase = step.get("current_phase", "")
    updated = step.get("updated_fields", {})

    # Update graph_state with newly produced fields
    gs = st.session_state.graph_state
    for key, val in updated.items():
        if val is not None:
            gs[key] = val

    gs["current_phase"] = phase

    # Final step — attach tool_trace and clean up
    if phase == "complete":
        if step.get("tool_trace"):
            gs["tool_trace"] = step["tool_trace"]
        st.session_state.streaming = False
        st.session_state.stream_gen = None
    else:
        st.session_state.streaming = True


def _render_streaming_status():
    """Render live Agent status cards using st.status()."""
    phase = st.session_state.graph_state.get("current_phase", "")
    phase_order = [a["phase"] for a in AGENT_STEPS]
    current_idx = phase_order.index(phase) if phase in phase_order else -1

    st.subheader("🤖 Agent 正在协作规划...")
    st.caption("四个智能体协同工作，实时展示执行进度")

    col1, col2 = st.columns([3, 1])
    with col2:
        if current_idx >= 0:
            pct = int((current_idx + 1) / len(AGENT_STEPS) * 100)
            st.progress(pct / 100, text=f"{pct}%")

    for agent in AGENT_STEPS:
        idx = phase_order.index(agent["phase"])
        with col1:
            if agent["phase"] == phase:
                # Currently running
                st.status(
                    f"{agent['icon']} **{agent['label']}** — {agent['desc']}",
                    state="running",
                )
            elif idx < current_idx or phase == "complete":
                # Completed
                st.status(
                    f"{agent['icon']} **{agent['label']}**  ✅ {agent['done']}",
                    state="complete",
                )
            else:
                # Waiting
                st.status(
                    f"{agent['icon']} **{agent['label']}**  ⏸️ 等待中",
                    state="error",
                )

    if current_idx >= 0:
        st.caption(f"步骤 {current_idx + 1} / {len(AGENT_STEPS)}")

    # Show any warning or error
    errors = st.session_state.graph_state.get("errors", [])
    if errors and phase != "complete":
        with st.expander("⚠️ 执行信息"):
            for err in errors:
                st.warning(err)

    # If complete, show a transition message
    if phase == "complete":
        st.success("🎉 所有 Agent 已完成！正在生成最终结果...")


# ── Form rendering ──


def _render_form():
    """Render the travel request input form."""
    gs = st.session_state.graph_state
    is_running = gs["current_phase"] not in ("idle", "complete", "error")

    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            destination = st.text_input(
                "目的地",
                value=st.session_state.get("_input_dest", ""),
                placeholder="例: 杭州",
                disabled=is_running,
                key="input_dest",
            )
        with col2:
            start_date = st.date_input(
                "出发日期",
                disabled=is_running,
                key="input_start",
            )
        with col3:
            end_date = st.date_input(
                "返回日期",
                disabled=is_running,
                key="input_end",
            )

        col1, col2, col3 = st.columns(3)
        with col1:
            travelers = st.number_input(
                "人数",
                min_value=1, max_value=20, value=2,
                disabled=is_running,
                key="input_travelers",
            )
        with col2:
            budget_min = st.number_input(
                "最低预算 (元)",
                min_value=0, max_value=100000, value=2000, step=500,
                disabled=is_running,
                key="input_budget_min",
            )
        with col3:
            budget_max = st.number_input(
                "最高预算 (元)",
                min_value=0, max_value=100000, value=5000, step=500,
                disabled=is_running,
                key="input_budget_max",
            )

        preferences = st.multiselect(
            "偏好标签",
            options=["景点", "美食", "购物", "文化", "户外", "夜生活", "娱乐"],
            default=["景点", "美食"],
            disabled=is_running,
            key="input_prefs",
        )

        notes = st.text_area(
            "补充需求 (选填)",
            placeholder="例: 带父母出行，希望行程不要太紧凑...",
            disabled=is_running,
            key="input_notes",
        )

        if is_running:
            st.info("⏳ Agent 正在执行中...")
            return

        if st.button("🚀 开始智能规划", use_container_width=True, type="primary"):
            if not destination.strip():
                st.error("请输入目的地")
                return

            form_input = {
                "destination": destination.strip(),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "travelers": int(travelers),
                "budget_min": float(budget_min),
                "budget_max": float(budget_max),
                "preferences": preferences,
                "notes": notes,
            }

            # Kick off streaming workflow
            st.session_state.stream_gen = get_workflow_stream(form_input)
            st.session_state.graph_state["current_phase"] = "parse"
            st.session_state.streaming = True
            st.rerun()
