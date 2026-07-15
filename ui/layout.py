import streamlit as st

from ui.result_map import render_map_tab
from ui.result_weather import render_weather_tab
from ui.result_timeline import render_timeline_tab
from ui.result_budget import render_budget_tab


def render_result_section():
    gs = st.session_state.graph_state
    if gs["current_phase"] != "complete" or gs["travel_plan"] is None:
        return

    st.subheader("📊 旅行结果")
    tp = gs["travel_plan"]

    st.success(tp.display_summary if hasattr(tp, "display_summary") else "规划完成")

    tabs = st.tabs(["🗺️ 地图", "☀️ 天气", "📅 行程", "💰 预算"])

    with tabs[0]:
        render_map_tab()

    with tabs[1]:
        render_weather_tab()

    with tabs[2]:
        render_timeline_tab()

    with tabs[3]:
        render_budget_tab()
