import streamlit as st

from config.theme import apply_theme
from models.state import init_session_state
from ui.top_bar import render_top_bar
from ui.input_section import render_input_section
from ui.pipeline_section import render_pipeline_section
from ui.tool_trace_section import render_tool_trace_section
from ui.layout import render_result_section
from ui.landing_section import render_landing_section


def main():
    st.set_page_config(
        page_title="AI Travel Agent",
        page_icon="🌍",
        layout="wide",
    )

    apply_theme()
    init_session_state()

    render_top_bar()

    gs = st.session_state.graph_state

    # Show landing section when idle
    if gs["current_phase"] == "idle":
        render_landing_section()

    render_input_section()

    if gs["current_phase"] != "idle":
        render_pipeline_section()
        render_tool_trace_section()
        render_result_section()

    if gs.get("errors"):
        with st.expander("❌ 执行错误", expanded=True):
            for err in gs["errors"]:
                st.error(err)


if __name__ == "__main__":
    main()
