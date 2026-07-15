import streamlit as st


def render_timeline_tab():
    gs = st.session_state.graph_state
    tp = gs.get("travel_plan")
    if not tp or not tp.days:
        st.info("暂无行程数据")
        return

    st.markdown("### 📅 行程时间线")

    st.info(tp.overview if tp.overview else f"📍 {tp.destination} · 共{tp.total_days}天行程")

    for day in tp.days:
        _render_day_timeline(day)

    if tp.notes:
        st.markdown("### 💡 出行提示")
        for note in tp.notes:
            st.markdown(f"- {note}")

    if tp.packing_tips:
        st.markdown("### 🎒 行李建议")
        st.markdown(" | ".join(f"`{tip}`" for tip in tp.packing_tips))


def _render_day_timeline(day):
    color = "#6366f1"
    st.markdown(
        f"""
    <div style="
        background-color: #1a1a24;
        border: 1px solid #2a2a3a;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    ">
        <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
            <span style="color:{color};font-weight:600;font-size:16px;">
                📍 {day.display_header}
            </span>
            <span style="color:#f59e0b;font-size:14px;">
                💰 ¥{day.daily_budget_estimate:.0f}
            </span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    for activity in day.activities:
        time_range = activity.time_slot.display
        cost = f" ¥{activity.estimated_cost:.0f}" if activity.estimated_cost else ""
        emoji = activity.emoji_category
        notes = ""
        if activity.notes:
            notes = " | " + " ".join(activity.notes)

        st.markdown(
            f"""
        <div style="
            display:flex;
            gap:12px;
            padding: 8px 0 8px 20px;
            border-left: 2px solid #2a2a3a;
            margin-left: 8px;
        ">
            <div style="color:#71717a;font-size:13px;min-width:100px;">{time_range}</div>
            <div>
                <div style="color:#e4e4e7;">{emoji} {activity.name}{cost}</div>
                <div style="color:#52525b;font-size:12px;">{notes}</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    if day.meals:
        for meal in day.meals:
            st.markdown(
                f"""<div style="
                display:flex;gap:12px;padding:4px 0 4px 20px;
                border-left: 2px solid #2a2a3a;margin-left:8px;
                color:#f59e0b;font-size:13px;
            ">{meal.display}</div>""",
                unsafe_allow_html=True,
            )

    acc = day.accommodation
    acc_cost = day.accommodation_cost
    if acc:
        st.markdown(
            f"""<div style="
            display:flex;gap:12px;padding:4px 0 4px 20px;
            border-left: 2px solid #2a2a3a;margin-left:8px;
            color:#22c55e;font-size:13px;
        ">🏨 住宿: {acc} {'¥{:.0f}'.format(acc_cost) if acc_cost else ''}</div>""",
            unsafe_allow_html=True,
        )

    if day.tips:
        for tip in day.tips:
            st.markdown(
                f"""<div style="
                display:flex;gap:12px;padding:2px 0 2px 20px;
                margin-left:8px;color:#71717a;font-size:12px;
            ">💡 {tip}</div>""",
                unsafe_allow_html=True,
            )
