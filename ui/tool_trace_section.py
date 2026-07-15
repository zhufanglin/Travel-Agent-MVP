import streamlit as st


def render_tool_trace_section():
    gs = st.session_state.graph_state
    traces = gs.get("tool_trace", [])
    if not traces:
        return

    st.subheader("📡 Agent Tool Trace — 工具调用时间线")
    st.caption("Researcher Agent 调用外部工具的完整记录 — Agent → Tool → Data")

    total = len(traces)
    success = sum(1 for t in traces if t["status"] == "success")
    total_ms = sum(t.get("duration_ms", 0) for t in traces)

    st.markdown(
        f"""
    <div style="display:flex;gap:24px;margin-bottom:16px;">
        <div style="background:#1a1a24;border:1px solid #2a2a3a;border-radius:8px;padding:12px 20px;text-align:center;">
            <div style="color:#71717a;font-size:11px;">工具调用</div>
            <div style="color:#e4e4e7;font-size:22px;font-weight:600;">{total}</div>
        </div>
        <div style="background:#1a1a24;border:1px solid #2a2a3a;border-radius:8px;padding:12px 20px;text-align:center;">
            <div style="color:#71717a;font-size:11px;">成功</div>
            <div style="color:#22c55e;font-size:22px;font-weight:600;">{success}</div>
        </div>
        <div style="background:#1a1a24;border:1px solid #2a2a3a;border-radius:8px;padding:12px 20px;text-align:center;">
            <div style="color:#71717a;font-size:11px;">总耗时</div>
            <div style="color:#f59e0b;font-size:22px;font-weight:600;">{total_ms}ms</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    expanded = st.session_state.ui_state["tool_trace_expanded"]
    label = f"详细调用记录 ({total} calls)"

    with st.expander(label, expanded=expanded):
        timeline_svg = _build_timeline_svg(traces)
        st.markdown(timeline_svg, unsafe_allow_html=True)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        for i, call in enumerate(traces):
            _render_tool_call_card(i, call)

    _render_memory_rag_badge(traces)


def _build_timeline_svg(traces):
    total_w = len(traces) * 120 + 40
    labels = ""
    bars = ""
    dots = ""
    times = ""
    for i, call in enumerate(traces):
        x = 40 + i * 120
        color = "#22c55e" if call["status"] == "success" else "#ef4444"
        duration = call.get("duration_ms", 0)
        pct = min(duration / 500, 1.0)

        bars += f"""
        <rect x="{x}" y="{150 - pct * 100}" width="30" height="{pct * 100}"
              rx="4" fill="{color}" opacity="0.8">
            <animate attributeName="height" from="0" to="{pct * 100}" dur="0.5s" begin="{i*0.15}s"/>
            <animate attributeName="y" from="150" to="{150 - pct * 100}" dur="0.5s" begin="{i*0.15}s"/>
        </rect>
        """
        dots += f"""
        <circle cx="{x + 15}" cy="160" r="4" fill="{color}">
            <animate attributeName="r" values="4;6;4" dur="2s" repeatCount="indefinite"
                     begin="{i*0.3}s"/>
        </circle>
        """
        name = call["tool_name"]
        if len(name) > 14:
            name = name[:12] + ".."
        labels += f"""
        <text x="{x + 15}" y="180" fill="#71717a" font-size="9" text-anchor="middle"
              transform="rotate(-20,{x + 15},180)">{name}</text>
        """
        times += f"""
        <text x="{x + 15}" y="140" fill="{color}" font-size="9" text-anchor="middle">{duration}ms</text>
        """

    return f"""
    <svg viewBox="0 0 {total_w} 210" width="100%" height="210" style="max-width:100%;">
        <text x="20" y="20" fill="#71717a" font-size="11" font-weight="600">⚡ 调用耗时 (ms)</text>
        <line x1="30" y1="150" x2="{total_w - 10}" y2="150" stroke="#2a2a3a" stroke-width="1"/>
        {bars}
        {dots}
        {labels}
        {times}
    </svg>
    """


def _render_tool_call_card(i, call):
    duration = call.get("duration_ms", 0)
    icon = "✅" if call["status"] == "success" else "❌"

    st.markdown(
        f"""
    <div style="
        background-color:#252530;
        border:1px solid #2a2a3a;
        border-left:3px solid {'#22c55e' if call['status']=='success' else '#ef4444'};
        border-radius:8px;
        padding:12px 16px;
        margin-bottom:8px;
    ">
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <div>
                <span style="color:#818cf8;font-weight:600;font-size:13px;">
                    #{i+1} {icon}
                </span>
                <span style="color:#f59e0b;font-family:monospace;font-size:13px;">
                    {call['tool_name']}
                </span>
            </div>
            <span style="color:#71717a;font-size:11px;">⏱ {duration}ms</span>
        </div>
        <div style="display:grid;grid-template-columns:80px 1fr;gap:4px;font-size:12px;">
            <span style="color:#71717a;">Input:</span>
            <span style="color:#a1a1aa;font-family:monospace;">{call['input']}</span>
            <span style="color:#71717a;">Output:</span>
            <span style="color:#a1a1aa;font-family:monospace;">{call['output']}</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def _render_memory_rag_badge(traces):
    st.markdown(
        """
    <div style="display:flex;gap:12px;margin-top:12px;flex-wrap:wrap;">
        <div style="background:#1a1a2e;border:1px solid #8b5cf644;border-radius:8px;
                    padding:8px 16px;display:flex;align-items:center;gap:8px;">
            <span style="font-size:16px;">📚</span>
            <span style="color:#a78bfa;font-size:12px;">RAG: 检索相似旅行案例 + 景点知识库</span>
        </div>
        <div style="background:#1a1a2e;border:1px solid #22c55e44;border-radius:8px;
                    padding:8px 16px;display:flex;align-items:center;gap:8px;">
            <span style="font-size:16px;">💾</span>
            <span style="color:#4ade80;font-size:12px;">Memory: 加载历史记录 (2条)</span>
        </div>
        <div style="background:#1a1a2e;border:1px solid #3b82f644;border-radius:8px;
                    padding:8px 16px;display:flex;align-items:center;gap:8px;">
            <span style="font-size:16px;">⚡</span>
            <span style="color:#60a5fa;font-size:12px;">Streaming: 实时进度推送</span>
        </div>
    </div>
    <div style="margin-top:8px;">
        <span style="color:#52525b;font-size:11px;">
            💡 注意: Agent 不是直接生成结果，而是通过 Tool → Data → LLM Analysis 的流程获取信息
        </span>
    </div>
    """,
        unsafe_allow_html=True,
    )
