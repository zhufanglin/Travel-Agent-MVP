import streamlit as st
from models.state import get_agent_status


PHASE_LABELS = {
    "idle": "⚪ 等待输入",
    "parse": "🧠 Coordinator 执行中",
    "research": "🔍 Researcher 执行中",
    "analyze": "📊 Analyst 执行中",
    "plan": "📋 Planner 执行中",
    "complete": "✅ 规划完成",
    "error": "❌ 执行出错",
}


def render_top_bar():
    gs = st.session_state.graph_state
    phase = gs["current_phase"]
    phase_label = PHASE_LABELS.get(phase, "⚪ 等待输入")
    provider_label = _get_provider_label()

    top_html = f"""
    <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:22px;">🌍</span>
            <span style="font-weight:700;font-size:20px;color:#e4e4e7;">AI Travel Agent</span>
            <span style="background:#1a1a2e;border:1px solid #6366f144;border-radius:12px;
                  padding:2px 10px;font-size:11px;color:#818cf8;">{provider_label}</span>
        </div>
        <div style="display:flex;align-items:center;gap:16px;">
            {_render_status_items()}
            <span style="color:#71717a;font-size:13px;border-left:1px solid #2a2a3a;padding-left:16px;">
                {phase_label}
            </span>
        </div>
    </div>
    """
    st.markdown(top_html, unsafe_allow_html=True)
    st.markdown("---")


def _render_status_items():
    agents = [
        ("coordinator", "🧠"),
        ("researcher", "🔍"),
        ("analyst", "📊"),
        ("planner", "📋"),
    ]
    items = ""
    for name, icon in agents:
        status = get_agent_status(name)
        items += f"""
        <div style="text-align:center;min-width:70px;">
            <div style="font-size:12px;color:#71717a;">{icon} {name.capitalize()}</div>
            <span style="color:{status['color']};font-size:11px;">{status['icon']} {status['label']}</span>
        </div>
        """
    return items


def _get_provider_label():
    try:
        from travel_agent.config import settings

        provider = (settings.LLM_PROVIDER or "openai").strip().lower()
        labels = {
            "deepseek": "DeepSeek 🐋",
            "openai": "OpenAI 🤖",
            "glm": "GLM 🧪",
        }
        return labels.get(provider, provider.upper())
    except Exception:
        return "LLM"
