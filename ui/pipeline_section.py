import streamlit as st
from models.state import get_agent_status, get_agent_output_summary

AGENT_CONFIG = [
    {"name": "coordinator", "label": "Coordinator Agent", "icon": "🧠", "desc": "需求理解与意图解析"},
    {"name": "researcher", "label": "Researcher Agent", "icon": "🔍", "desc": "信息采集与工具调用"},
    {"name": "analyst", "label": "Analyst Agent", "icon": "📊", "desc": "数据分析与推荐评分"},
    {"name": "planner", "label": "Planner Agent", "icon": "📋", "desc": "行程编排与预算规划"},
]


def render_pipeline_section():
    gs = st.session_state.graph_state
    if gs["current_phase"] == "idle":
        return

    st.subheader("🔄 多Agent协作流水线")
    st.caption("四个智能体协同工作，逐步完成旅行规划")

    cols = st.columns(4)
    for idx, (col, agent) in enumerate(zip(cols, AGENT_CONFIG)):
        with col:
            _render_agent_card(agent, idx)

    st.markdown("---")


def _render_agent_card(agent: dict, idx: int):
    status = get_agent_status(agent["name"])
    output = get_agent_output_summary(agent["name"])

    border_color = status["color"]
    st.markdown(
        f"""
    <div style="
        background-color: #1a1a24;
        border: 1px solid {border_color}44;
        border-left: 4px solid {border_color};
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    ">
        <div style="font-size: 24px; margin-bottom: 4px;">{agent['icon']}</div>
        <div style="font-weight: 600; color: #e4e4e7; font-size: 15px;">{agent['label']}</div>
        <div style="color: #71717a; font-size: 12px; margin-bottom: 8px;">{agent['desc']}</div>
        <div style="color: {status['color']}; font-size: 13px; margin-bottom: 6px;">
            {status['icon']} {status['label']}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if output:
        st.markdown(
            f"<div style='color:#a1a1aa;font-size:12px;padding:4px 8px;"
            f"background:#252530;border-radius:6px;'>{output}</div>",
            unsafe_allow_html=True,
        )

    if idx < 3:
        st.markdown(
            "<div style='text-align:center;color:#52525b;font-size:20px;'>↓</div>",
            unsafe_allow_html=True,
        )
