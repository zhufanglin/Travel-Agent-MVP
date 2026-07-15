"""Preference learning — extracts user preferences from TravelIntent and TravelPlan.

Learns:
  - cuisine_preferences: food-related interests
  - interest_preferences: POI category interests
  - budget_habits: budget range and level
  - companion_habits: typical travel group size
"""

from travel_agent.schemas.common import POICategory
from travel_agent.schemas.plan import TravelPlan
from travel_agent.schemas.travel import TravelIntent

from travel_agent.memory.user_profile import UserProfileStore


# ── Category mappings for learning ──

_CUISINE_KEYWORDS: dict[str, str] = {
    "川菜": "川菜", "湘菜": "湘菜", "粤菜": "粤菜",
    "日料": "日料", "韩餐": "韩餐", "西餐": "西餐",
    "火锅": "火锅", "烧烤": "烧烤", "小吃": "小吃",
    "海鲜": "海鲜", "素食": "素食", "甜品": "甜品",
    "咖啡": "咖啡", "茶": "茶饮",
}

_INTEREST_LABELS: dict[POICategory, str] = {
    POICategory.ATTRACTION: "景点",
    POICategory.RESTAURANT: "美食",
    POICategory.MUSEUM: "文化场馆",
    POICategory.SHOPPING: "购物",
    POICategory.PARK: "自然风光",
    POICategory.ENTERTAINMENT: "娱乐",
    POICategory.NIGHTLIFE: "夜生活",
    POICategory.HOTEL: "住宿品质",
}


class PreferenceLearner:
    """Extracts and persists user preferences from trips."""

    def __init__(self, store: UserProfileStore):
        self.store = store

    def learn_from_intent(self, intent: TravelIntent, confidence: float = 0.6):
        """Extract preferences from a TravelIntent and save them.

        Called after each successful trip planning.
        """
        prefs = intent.preferences
        if not prefs:
            return

        # ── Interest preferences ──
        for cat in prefs.interests:
            label = _INTEREST_LABELS.get(cat)
            if label:
                self.store.save_preference("interest", label, confidence)

        # ── Cuisine preferences ──
        for cuisine in prefs.cuisine_preferences:
            matched = _CUISINE_KEYWORDS.get(cuisine)
            if matched:
                self.store.save_preference("cuisine", matched, confidence)

        # ── Pace preference ──
        if prefs.pace:
            pace_labels = {"relaxed": "轻松", "moderate": "适中", "intensive": "紧凑"}
            label = pace_labels.get(prefs.pace)
            if label:
                self.store.save_preference("pace", label, confidence * 0.8)

    def learn_from_plan(self, intent: TravelIntent, plan: TravelPlan, confidence: float = 0.8):
        """Extract deeper preferences from the finalized travel plan."""
        # ── Budget habit ──
        if intent.budget and intent.budget.max_amount > 0:
            budget = intent.budget
            avg_per_person = budget.max_amount / max(intent.companions, 1)
            if avg_per_person < 1000:
                level = "经济型"
            elif avg_per_person < 3000:
                level = "舒适型"
            else:
                level = "豪华型"
            self.store.save_preference("budget_level", level, confidence * 0.7)

        # ── Companion habit ──
        if intent.companions > 0:
            if intent.companions == 1:
                label = "独自出行"
            elif intent.companions == 2:
                label = "双人出行"
            elif intent.companions <= 4:
                label = "小团体出行"
            else:
                label = "多人出行"
            self.store.save_preference("companions", label, confidence * 0.6)

    def learn_from_interaction(self, intent: TravelIntent, plan: TravelPlan):
        """Full learning pipeline from a completed interaction."""
        self.learn_from_intent(intent, confidence=0.6)
        self.learn_from_plan(intent, plan, confidence=0.8)
