import streamlit as st
from datetime import date


def render_weather_tab():
    gs = st.session_state.graph_state
    research = gs.get("research_report")
    if not research or not research.weather.forecasts:
        st.info("暂无天气数据")
        return

    forecasts = research.weather.forecasts
    summary = research.weather.overall_summary

    st.markdown("### ☀️ 天气分析")

    if summary:
        st.info(summary)

    cols = st.columns(len(forecasts))
    for col, f in zip(cols, forecasts):
        with col:
            cond = f.condition
            date_str = f.forecast_date
            if isinstance(date_str, date):
                date_str = date_str.strftime("%m/%d")

            st.markdown(
                f"""
            <div style="
                background-color: #1a1a24;
                border: 1px solid #2a2a3a;
                border-radius: 12px;
                padding: 16px;
                text-align: center;
            ">
                <div style="color: #71717a; font-size: 13px;">{date_str}</div>
                <div style="font-size: 36px; margin: 8px 0;">{cond.emoji}</div>
                <div style="color: #e4e4e7; font-size: 13px;">{cond.label_cn}</div>
                <div style="color: #f59e0b; font-size: 16px; font-weight: 600;">
                    {f.temperature_high:.0f}°C
                </div>
                <div style="color: #3b82f6; font-size: 14px;">
                    {f.temperature_low:.0f}°C
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("### 📈 温度趋势")

    try:
        import plotly.graph_objects as go

        dates = []
        highs = []
        lows = []
        conditions = []

        for f in forecasts:
            d = f.forecast_date
            if isinstance(d, date):
                dates.append(d.strftime("%m/%d"))
            else:
                dates.append(str(d))
            highs.append(f.temperature_high)
            lows.append(f.temperature_low)
            conditions.append(f"{f.condition.emoji} {f.condition.label_cn}")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=highs, mode="lines+markers",
            name="最高温", line=dict(color="#f59e0b", width=3),
            marker=dict(size=8, color="#f59e0b"),
            hovertemplate="%{x}<br>最高: %{y}°C<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=lows, mode="lines+markers",
            name="最低温", line=dict(color="#3b82f6", width=3),
            marker=dict(size=8, color="#3b82f6"),
            hovertemplate="%{x}<br>最低: %{y}°C<extra></extra>",
        ))

        fig.update_layout(
            template="plotly_dark",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=20, b=20),
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#a1a1aa"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig.update_xaxes(gridcolor="#2a2a3a")
        fig.update_yaxes(gridcolor="#2a2a3a")

        st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        st.warning("plotly 未安装，使用表格展示温度数据")
        data = []
        for f in forecasts:
            d = f.forecast_date
            if isinstance(d, date):
                d = d.strftime("%m/%d")
            data.append({
                "日期": d,
                "天气": f"{f.condition.emoji} {f.condition.label_cn}",
                "最高温": f"{f.temperature_high:.0f}°C",
                "最低温": f"{f.temperature_low:.0f}°C",
            })
        st.table(data)

    st.caption("💡 天气数据来源: 百度天气查询服务")
