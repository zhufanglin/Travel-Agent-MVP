import streamlit as st


def render_budget_tab():
    gs = st.session_state.graph_state
    tp = gs.get("travel_plan")
    if not tp:
        st.info("暂无预算数据")
        return

    budget = tp.budget_breakdown

    st.markdown("### 💰 预算分析")

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown(f"**总预算: ¥{budget.total_estimated:,.0f}**")
        try:
            import plotly.graph_objects as go

            items = budget.breakdown_items
            colors = ["#6366f1", "#f59e0b", "#3b82f6", "#22c55e", "#ef4444"]

            fig = go.Figure(data=[
                go.Pie(
                    labels=list(items.keys()),
                    values=list(items.values()),
                    hole=0.4,
                    marker=dict(colors=colors[:len(items)]),
                    textinfo="label+percent",
                    textfont=dict(color="#e4e4e7"),
                    hovertemplate="%{label}: ¥%{value:,.0f}<extra></extra>",
                )
            ])
            fig.update_layout(
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#a1a1aa"),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        except ImportError:
            items = budget.breakdown_items
            for label, amount in items.items():
                pct = (amount / budget.total_estimated * 100) if budget.total_estimated else 0
                st.markdown(f"- {label}: ¥{amount:,.0f} ({pct:.0f}%)")

    with col2:
        st.markdown("**费用明细**")
        items = budget.breakdown_items
        total = sum(items.values()) or 1
        for label, amount in items.items():
            pct = amount / total * 100
            st.markdown(
                f"""
            <div style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;color:#a1a1aa;font-size:13px;">
                    <span>{label}</span>
                    <span>¥{amount:,.0f}</span>
                </div>
                <div style="background-color:#2a2a3a;border-radius:4px;height:8px;margin-top:4px;">
                    <div style="
                        background-color:{['#6366f1','#f59e0b','#3b82f6','#22c55e','#ef4444'][list(items.keys()).index(label)]};
                        width:{pct:.0f}%;
                        height:8px;
                        border-radius:4px;
                    "></div>
                </div>
                <div style="text-align:right;color:#52525b;font-size:11px;">{pct:.0f}%</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("**每日费用参考**")
    if tp.days:
        for day in tp.days:
            bar_width = (day.daily_budget_estimate / budget.total_estimated * 100) if budget.total_estimated else 0
            st.markdown(
                f"""
            <div style="margin-bottom:8px;">
                <div style="display:flex;justify-content:space-between;color:#a1a1aa;font-size:13px;">
                    <span>{day.display_header}</span>
                    <span>¥{day.daily_budget_estimate:,.0f}</span>
                </div>
                <div style="background-color:#2a2a3a;border-radius:4px;height:6px;margin-top:2px;">
                    <div style="
                        background:linear-gradient(90deg, #6366f1, #818cf8);
                        width:{bar_width:.0f}%;
                        height:6px;
                        border-radius:4px;
                    "></div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.caption("💰 预算数据综合自行程规划和市场参考价格")
