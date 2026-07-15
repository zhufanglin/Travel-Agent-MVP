"""Mock place search tool — returns realistic POI data for popular Chinese cities.

MVP uses mock data. Structure matches travel_agent.schemas.common.POI.
Replace with real LBS API (Amap / Baidu Maps) in Phase 2.
"""

from typing import Optional

from travel_agent.schemas.common import (
    Coordinate,
    GeoLocation,
    POI,
    POICategory,
)

# ── Rich mock data for common destinations ──

_MOCK_PLACES: dict[str, list[dict]] = {
    "北京": [
        {
            "name": "故宫博物院",
            "category": POICategory.ATTRACTION,
            "subcategory": "历史博物馆",
            "address": "北京市东城区景山前街4号",
            "lat": 39.9163, "lng": 116.3972,
            "rating": 4.8, "avg_cost": 60,
            "opening_hours": "08:30-17:00 (周一闭馆)",
            "tags": ["历史文化", "世界遗产", "拍照打卡"],
        },
        {
            "name": "八达岭长城",
            "category": POICategory.ATTRACTION,
            "subcategory": "历史古迹",
            "address": "北京市延庆区G6京藏高速58号出口",
            "lat": 40.3541, "lng": 116.0037,
            "rating": 4.7, "avg_cost": 40,
            "opening_hours": "07:30-16:00",
            "tags": ["历史文化", "户外", "世界遗产"],
        },
        {
            "name": "全聚德烤鸭(前门店)",
            "category": POICategory.RESTAURANT,
            "subcategory": "北京烤鸭",
            "address": "北京市东城区前门大街32号",
            "lat": 39.8952, "lng": 116.3956,
            "rating": 4.4, "avg_cost": 200,
            "opening_hours": "11:00-21:00",
            "tags": ["北京烤鸭", "老字号", "必吃"],
        },
        {
            "name": "南锣鼓巷",
            "category": POICategory.SHOPPING,
            "subcategory": "特色街区",
            "address": "北京市东城区南锣鼓巷",
            "lat": 39.9370, "lng": 116.4025,
            "rating": 4.2, "avg_cost": 80,
            "tags": ["逛街", "小吃", "文艺"],
        },
        {
            "name": "北京王府井希尔顿酒店",
            "category": POICategory.HOTEL,
            "subcategory": "五星酒店",
            "address": "北京市东城区王府井东街8号",
            "lat": 39.9138, "lng": 116.4106,
            "rating": 4.6, "avg_cost": 800,
            "tags": ["豪华", "市中心", "商务"],
        },
        {
            "name": "天坛公园",
            "category": POICategory.PARK,
            "subcategory": "皇家园林",
            "address": "北京市东城区天坛内东里7号",
            "lat": 39.8822, "lng": 116.4066,
            "rating": 4.7, "avg_cost": 15,
            "opening_hours": "06:00-21:00",
            "tags": ["历史文化", "公园", "世界遗产"],
        },
        {
            "name": "三里屯太古里",
            "category": POICategory.ENTERTAINMENT,
            "subcategory": "商业街区",
            "address": "北京市朝阳区三里屯路19号",
            "lat": 39.9333, "lng": 116.4551,
            "rating": 4.3, "avg_cost": 300,
            "tags": ["逛街", "时尚", "夜生活"],
        },
        {
            "name": "国家博物馆",
            "category": POICategory.MUSEUM,
            "subcategory": "综合博物馆",
            "address": "北京市东城区东长安街16号",
            "lat": 39.9054, "lng": 116.3976,
            "rating": 4.6, "avg_cost": 0,
            "opening_hours": "09:00-17:00 (周一闭馆)",
            "tags": ["历史文化", "免费", "室内"],
        },
    ],
    "上海": [
        {
            "name": "外滩",
            "category": POICategory.ATTRACTION,
            "subcategory": "城市景观",
            "address": "上海市黄浦区中山东一路",
            "lat": 31.2400, "lng": 121.4900,
            "rating": 4.7, "avg_cost": 0,
            "tags": ["城市风光", "夜景", "免费"],
        },
        {
            "name": "上海迪士尼乐园",
            "category": POICategory.ENTERTAINMENT,
            "subcategory": "主题乐园",
            "address": "上海市浦东新区川沙镇黄赵路310号",
            "lat": 31.1433, "lng": 121.6544,
            "rating": 4.8, "avg_cost": 475,
            "opening_hours": "08:30-20:30",
            "tags": ["亲子", "游乐", "热门"],
        },
        {
            "name": "南京路步行街",
            "category": POICategory.SHOPPING,
            "subcategory": "商业街",
            "address": "上海市黄浦区南京东路",
            "lat": 31.2360, "lng": 121.4750,
            "rating": 4.3, "avg_cost": 200,
            "tags": ["逛街", "美食", "购物"],
        },
        {
            "name": "豫园",
            "category": POICategory.ATTRACTION,
            "subcategory": "古典园林",
            "address": "上海市黄浦区豫园老街279号",
            "lat": 31.2272, "lng": 121.4943,
            "rating": 4.4, "avg_cost": 40,
            "tags": ["古典园林", "文化", "美食"],
        },
    ],
    "成都": [
        {
            "name": "大熊猫繁育研究基地",
            "category": POICategory.ATTRACTION,
            "subcategory": "动物园",
            "address": "成都市成华区熊猫大道1375号",
            "lat": 30.7360, "lng": 104.1430,
            "rating": 4.8, "avg_cost": 55,
            "opening_hours": "07:30-18:00",
            "tags": ["熊猫", "亲子", "必去"],
        },
        {
            "name": "宽窄巷子",
            "category": POICategory.ATTRACTION,
            "subcategory": "历史文化街区",
            "address": "成都市青羊区长顺街",
            "lat": 30.6700, "lng": 104.0550,
            "rating": 4.4, "avg_cost": 0,
            "tags": ["文化", "美食", "拍照"],
        },
        {
            "name": "小龙坎老火锅(春熙路店)",
            "category": POICategory.RESTAURANT,
            "subcategory": "火锅",
            "address": "成都市锦江区东大街188号",
            "lat": 30.6570, "lng": 104.0820,
            "rating": 4.5, "avg_cost": 120,
            "tags": ["火锅", "必吃", "辣"],
        },
    ],
    "广州": [
        {
            "name": "广州塔",
            "category": POICategory.ATTRACTION,
            "subcategory": "城市地标",
            "address": "广州市海珠区阅江西路222号",
            "lat": 23.1065, "lng": 113.3245,
            "rating": 4.5, "avg_cost": 150,
            "opening_hours": "09:30-22:00",
            "tags": ["城市风光", "夜景", "地标"],
        },
        {
            "name": "长隆野生动物世界",
            "category": POICategory.ENTERTAINMENT,
            "subcategory": "主题乐园",
            "address": "广州市番禺区汉溪大道东299号",
            "lat": 23.0000, "lng": 113.3200,
            "rating": 4.7, "avg_cost": 300,
            "tags": ["亲子", "动物", "游乐"],
        },
        {
            "name": "陶陶居(上下九店)",
            "category": POICategory.RESTAURANT,
            "subcategory": "粤菜",
            "address": "广州市荔湾区上下九步行街",
            "lat": 23.1200, "lng": 113.2500,
            "rating": 4.3, "avg_cost": 100,
            "tags": ["早茶", "粤菜", "老字号"],
        },
    ],
    "杭州": [
        {
            "name": "西湖风景区",
            "category": POICategory.ATTRACTION,
            "subcategory": "湖泊",
            "address": "杭州市西湖区",
            "lat": 30.2590, "lng": 120.1450,
            "rating": 4.8, "avg_cost": 0,
            "tags": ["必去", "世界遗产", "拍照打卡"],
        },
        {
            "name": "灵隐寺",
            "category": POICategory.ATTRACTION,
            "subcategory": "寺庙",
            "address": "杭州市西湖区灵隐路",
            "lat": 30.2440, "lng": 120.1000,
            "rating": 4.6, "avg_cost": 75,
            "tags": ["历史", "宗教", "文化"],
        },
        {
            "name": "雷峰塔",
            "category": POICategory.ATTRACTION,
            "subcategory": "古塔",
            "address": "杭州市西湖区南山路",
            "lat": 30.2330, "lng": 120.1480,
            "rating": 4.5, "avg_cost": 40,
            "tags": ["文化", "观景", "神话"],
        },
        {
            "name": "楼外楼(孤山路店)",
            "category": POICategory.RESTAURANT,
            "subcategory": "杭帮菜",
            "address": "杭州市西湖区孤山路30号",
            "lat": 30.2600, "lng": 120.1480,
            "rating": 4.4, "avg_cost": 180,
            "tags": ["老字号", "西湖醋鱼", "杭帮菜"],
        },
        {
            "name": "外婆家(杭州大厦店)",
            "category": POICategory.RESTAURANT,
            "subcategory": "杭帮菜",
            "address": "杭州市下城区武林广场21号",
            "lat": 30.2750, "lng": 120.1650,
            "rating": 4.2, "avg_cost": 80,
            "tags": ["平价", "杭帮菜", "排队王"],
        },
        {
            "name": "断桥残雪",
            "category": POICategory.ATTRACTION,
            "subcategory": "景点",
            "address": "杭州市西湖区北山路",
            "lat": 30.2570, "lng": 120.1500,
            "rating": 4.7, "avg_cost": 0,
            "tags": ["西湖十景", "文化", "拍照"],
        },
        {
            "name": "河坊街",
            "category": POICategory.SHOPPING,
            "subcategory": "商业街",
            "address": "杭州市上城区河坊街",
            "lat": 30.2410, "lng": 120.1670,
            "rating": 4.3, "avg_cost": 100,
            "tags": ["特色小吃", "购物", "历史文化"],
        },
        {
            "name": "西溪国家湿地公园",
            "category": POICategory.PARK,
            "subcategory": "湿地公园",
            "address": "杭州市西湖区天目山路518号",
            "lat": 30.2700, "lng": 120.0700,
            "rating": 4.5, "avg_cost": 80,
            "tags": ["自然", "徒步", "生态"],
        },
    ],
}

_DEFAULT_CITY = "北京"


def search_places(
    destination: str,
    categories: Optional[list[POICategory]] = None,
    keywords: Optional[list[str]] = None,
) -> list[POI]:
    """Search for Points of Interest in a destination city.

    Args:
        destination: City name (Chinese).
        categories: Filter by POI categories. If None, return all.
        keywords: Optional keywords to filter by tags/name.

    Returns:
        List of POI objects matching the criteria.
    """
    raw_places = _MOCK_PLACES.get(destination, _MOCK_PLACES.get(_DEFAULT_CITY, []))

    pois: list[POI] = []
    for item in raw_places:
        if categories and item["category"] not in categories:
            continue
        if keywords:
            name_match = any(kw in item["name"] for kw in keywords)
            tag_match = any(kw in t for t in item["tags"] for kw in keywords)
            if not name_match and not tag_match:
                continue

        poi = POI(
            name=item["name"],
            category=item["category"],
            subcategory=item.get("subcategory", ""),
            location=GeoLocation(
                name=item["name"],
                address=item["address"],
                coordinate=Coordinate(lat=item["lat"], lng=item["lng"]),
                city=destination,
            ),
            rating=item.get("rating"),
            avg_cost=item.get("avg_cost"),
            opening_hours=item.get("opening_hours"),
            tags=item.get("tags", []),
            description=item.get("description", ""),
            source="mock-lbs-service",
        )
        pois.append(poi)

    return pois
