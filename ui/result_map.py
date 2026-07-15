import streamlit as st


def render_map_tab():
    gs = st.session_state.graph_state
    research = gs.get("research_report")
    if not research:
        st.info("暂无地图数据")
        return

    pois = research.pois.all_pois
    tp = gs.get("travel_plan")

    st.markdown("### 🗺️ 百度地图 — 路线与景点")

    with st.container():
        try:
            import folium
            from streamlit_folium import st_folium

            center_lat = 30.2741
            center_lng = 120.1551

            m = folium.Map(
                location=[center_lat, center_lng],
                zoom_start=13,
                tiles="https://mt.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                attr="Google Maps",
            )

            for poi in pois:
                if poi.location and poi.location.coordinate:
                    icon_color = "red"
                    if poi.category.value == "restaurant":
                        icon_color = "orange"
                    elif poi.category.value == "shopping":
                        icon_color = "green"
                    elif poi.category.value == "park":
                        icon_color = "blue"

                    popup_text = f"""
                    <b>{poi.display_name}</b><br>
                    {poi.description}<br>
                    {'⭐' * round(poi.rating) if poi.rating else ''} {poi.rating if poi.rating else ''}
                    """

                    folium.Marker(
                        location=[poi.location.coordinate.lat, poi.location.coordinate.lng],
                        popup=folium.Popup(popup_text, max_width=250),
                        icon=folium.Icon(color=icon_color, icon="info-sign"),
                    ).add_to(m)

            if tp and tp.days:
                route_points = []
                for day in tp.days:
                    for activity in day.activities:
                        loc = activity.location
                        if loc and loc.coordinate:
                            route_points.append([loc.coordinate.lat, loc.coordinate.lng])

                if len(route_points) >= 2:
                    folium.PolyLine(
                        route_points, color="#6366f1", weight=3, opacity=0.7, dash_array="10"
                    ).add_to(m)

            st_folium(m, width=None, height=500)

            st.caption("📍 红色=景点 | 橙色=餐厅 | 绿色=购物 | 蓝色=公园 | 紫色连线=规划路线")

        except ImportError:
            st.warning("streamlit-folium 未安装，使用表格展示 POI 数据")
            _render_poi_table(pois)

    if tp and tp.days:
        with st.expander("查看路线详情"):
            for day in tp.days:
                st.markdown(f"**{day.display_header}**")
                for activity in day.activities:
                    loc_name = activity.location.name if activity.location else ""
                    time_str = activity.time_slot.display
                    st.markdown(f"- {time_str} | {activity.name} {f'📍{loc_name}' if loc_name else ''}")


def _render_poi_table(pois):
    data = []
    for p in pois:
        data.append({
            "名称": p.display_name,
            "类别": p.category.label_cn,
            "评分": f"{p.rating}/5" if p.rating else "暂无",
            "地址": p.location.address if p.location else "",
        })
    st.table(data)
