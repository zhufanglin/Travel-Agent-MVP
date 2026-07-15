"""Tests for the Memory module — UserProfileStore, PreferenceLearner, MemoryManager.

Uses a temporary SQLite database to avoid polluting the real one.
"""

import os
import tempfile
from datetime import date

import pytest

from travel_agent.memory.memory_manager import MemoryManager
from travel_agent.memory.preference_store import PreferenceLearner
from travel_agent.memory.user_profile import TravelRecord, UserProfileStore
from travel_agent.schemas.common import POICategory, Budget
from travel_agent.schemas.plan import BudgetBreakdown, DayPlan, TravelPlan
from travel_agent.schemas.travel import TravelIntent, TravelPreferences


@pytest.fixture
def db_path():
    """Temporary SQLite database path for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    try:
        # Force garbage collection to release SQLite locks on Windows
        import gc
        gc.collect()
        os.unlink(path)
    except PermissionError:
        pass  # Windows: file lock race, best-effort cleanup


@pytest.fixture
def store(db_path) -> UserProfileStore:
    return UserProfileStore(db_path)


@pytest.fixture
def learner(store) -> PreferenceLearner:
    return PreferenceLearner(store)


@pytest.fixture
def memory_manager(db_path) -> MemoryManager:
    return MemoryManager(db_path)


@pytest.fixture
def sample_intent() -> TravelIntent:
    return TravelIntent(
        destination="成都",
        duration_days=4,
        companions=2,
        budget=Budget(min_amount=2000, max_amount=5000, currency="CNY"),
        preferences=TravelPreferences(
            interests=[POICategory.ATTRACTION, POICategory.RESTAURANT, POICategory.MUSEUM],
            cuisine_preferences=["川菜", "火锅"],
            pace="moderate",
        ),
    )


@pytest.fixture
def sample_plan() -> TravelPlan:
    return TravelPlan(
        title="成都4日游",
        destination="成都",
        days=[DayPlan(day_index=i, title=f"Day {i+1}") for i in range(4)],
        budget_breakdown=BudgetBreakdown(
            total_estimated=4000,
            accommodation_total=1200,
            food_total=1000,
            transportation_total=800,
            activities_total=600,
            miscellaneous_total=400,
        ),
    )


# ──────────────────────────────────────────────
#  1. UserProfileStore Tests
# ──────────────────────────────────────────────


class TestUserProfileStore:
    def test_new_user_has_no_preferences(self, store):
        """Newly created store should have empty profile."""
        profile = store.get_profile()
        assert profile.is_new_user
        assert profile.total_trips == 0
        assert len(profile.preferences) == 0

    def test_save_and_retrieve_preferences(self, store):
        """Preferences should persist after save."""
        store.save_preference("cuisine", "川菜", confidence=0.8)
        store.save_preference("interest", "景点", confidence=0.9)

        prefs = store.get_preferences()
        assert len(prefs) == 2
        assert prefs[0].category == "interest"  # highest confidence first

        cuisine_prefs = store.get_preferences("cuisine")
        assert len(cuisine_prefs) == 1
        assert cuisine_prefs[0].value == "川菜"

    def test_preference_upsert(self, store):
        """Saving same category+value should update confidence."""
        store.save_preference("cuisine", "川菜", confidence=0.5)
        store.save_preference("cuisine", "川菜", confidence=0.9)

        prefs = store.get_preferences("cuisine")
        assert len(prefs) == 1  # not duplicated
        assert prefs[0].confidence == 0.9

    def test_travel_history_roundtrip(self, store):
        """Travel records should persist and be retrievable."""
        record = TravelRecord(
            destination="北京",
            duration_days=3,
            companions=2,
            budget_total=3000,
            interests=["景点", "美食"],
        )
        store.save_travel_record(record)

        history = store.get_travel_history()
        assert len(history) == 1
        assert history[0].destination == "北京"
        assert history[0].duration_days == 3
        assert "景点" in history[0].interests

    def test_profile_aggregation(self, store):
        """Profile should aggregate multiple records correctly."""
        store.save_travel_record(TravelRecord(destination="北京", companions=2, interests=["景点"]))
        store.save_travel_record(TravelRecord(destination="上海", companions=2, interests=["美食"]))
        store.save_travel_record(TravelRecord(destination="北京", companions=2, interests=["景点"]))

        profile = store.get_profile()
        assert profile.total_trips == 3
        assert profile.frequent_destinations[0] == "北京"
        assert profile.typical_companions == 2

    def test_clear_all(self, store):
        """Clear should remove all data."""
        store.save_preference("cuisine", "川菜")
        store.save_travel_record(TravelRecord(destination="北京"))
        store.clear_all()

        profile = store.get_profile()
        assert profile.is_new_user


# ──────────────────────────────────────────────
#  2. PreferenceLearner Tests
# ──────────────────────────────────────────────


class TestPreferenceLearner:
    def test_learn_interests_from_intent(self, learner, sample_intent):
        """Learner should extract POI category interests."""
        learner.learn_from_intent(sample_intent)

        prefs = learner.store.get_preferences("interest")
        values = [p.value for p in prefs]
        assert "景点" in values
        assert "美食" in values
        assert "文化场馆" in values

    def test_learn_cuisine_from_intent(self, learner, sample_intent):
        """Learner should extract cuisine preferences."""
        learner.learn_from_intent(sample_intent)

        prefs = learner.store.get_preferences("cuisine")
        values = [p.value for p in prefs]
        assert "川菜" in values
        assert "火锅" in values

    def test_learn_budget_from_plan(self, learner, sample_intent, sample_plan):
        """Learner should extract budget level."""
        learner.learn_from_plan(sample_intent, sample_plan)

        prefs = learner.store.get_preferences("budget_level")
        assert len(prefs) > 0

    def test_full_learning_pipeline(self, learner, sample_intent, sample_plan):
        """Full learn_from_interaction should save all categories."""
        learner.learn_from_interaction(sample_intent, sample_plan)

        prefs = learner.store.get_preferences()
        categories = {p.category for p in prefs}
        assert "interest" in categories
        assert "cuisine" in categories
        assert "budget_level" in categories


# ──────────────────────────────────────────────
#  3. MemoryManager Tests
# ──────────────────────────────────────────────


class TestMemoryManager:
    def test_new_user_returns_empty_context(self, memory_manager):
        """New user should get empty memory context."""
        ctx = memory_manager.get_memory_context()
        assert ctx == ""

    def test_context_includes_history(self, memory_manager, sample_intent, sample_plan):
        """After saving, context should include learned preferences."""
        memory_manager.save_from_result(sample_intent, sample_plan)
        ctx = memory_manager.get_memory_context()

        assert "=== 你的旅行记忆 ===" in ctx
        assert "成都" in ctx
        assert "景点" in ctx or "美食" in ctx

    def test_context_formatting(self, memory_manager, sample_intent, sample_plan):
        """Context should use emoji icons and structured sections."""
        memory_manager.save_from_result(sample_intent, sample_plan)
        ctx = memory_manager.get_memory_context()

        assert "🍽️" in ctx or "🏛️" in ctx or "👥" in ctx or "📅" in ctx
        assert "===================" in ctx

    def test_save_from_result_with_intent_and_plan(self, memory_manager, sample_intent, sample_plan):
        """save_from_result should persist both preferences and history."""
        memory_manager.save_from_result(sample_intent, sample_plan)

        profile = memory_manager.get_profile()
        assert profile.total_trips == 1
        assert len(profile.preferences) > 0

    def test_multiple_sessions_accumulate(self, memory_manager, sample_intent, sample_plan):
        """Multiple trips should accumulate in history."""
        memory_manager.save_from_result(sample_intent, sample_plan)
        memory_manager.save_from_result(sample_intent, sample_plan)

        profile = memory_manager.get_profile()
        assert profile.total_trips == 2

    def test_context_shows_frequent_destinations(self, memory_manager):
        """Context should highlight frequently visited cities."""
        for dest in ["北京", "北京", "上海"]:
            memory_manager.store.save_travel_record(TravelRecord(destination=dest))

        ctx = memory_manager.get_memory_context()
        assert "北京" in ctx
        assert "上海" in ctx

    def test_clear_memory(self, memory_manager, sample_intent, sample_plan):
        """Clear should reset all stored data."""
        memory_manager.save_from_result(sample_intent, sample_plan)
        memory_manager.clear()
        assert memory_manager.get_memory_context() == ""
