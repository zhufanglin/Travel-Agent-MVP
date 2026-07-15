"""Memory Manager — facade for the memory subsystem.

Used by the adapter (services/agent_interface.py) to:
  1. Retrieve memory context before each planning session
  2. Save learned preferences after each planning session
  3. Save travel history after each planning session
"""

from datetime import date
from pathlib import Path
from typing import Optional

from travel_agent.memory.preference_store import PreferenceLearner
from travel_agent.memory.user_profile import TravelRecord, UserProfile, UserProfileStore


class MemoryManager:
    """Facade for memory retrieval and storage.

    Usage:
        mm = MemoryManager()
        ctx = mm.get_memory_context()          # Returns formatted string
        mm.save_from_result(intent, plan)       # Saves after planning
    """

    def __init__(self, db_path: Optional[str | Path] = None):
        self.store = UserProfileStore(db_path) if db_path else UserProfileStore()
        self.learner = PreferenceLearner(self.store)

    # ── Retrieval ──

    def get_profile(self) -> UserProfile:
        """Get the full aggregated user profile."""
        return self.store.get_profile()

    def get_memory_context(self) -> str:
        """Build a formatted memory string for Coordinator context injection.

        Returns a multi-line string like:
            === 你的旅行记忆 ===
            🍽️ 美食偏好: 川菜
            🏛️ 兴趣偏好: 景点、文化场馆
            ...

        Empty if the user has no history.
        """
        profile = self.store.get_profile()
        if profile.is_new_user:
            return ""

        lines = ["\n=== 你的旅行记忆 ==="]

        # Preferences
        prefs_by_cat: dict[str, list[str]] = {}
        for p in profile.preferences:
            if p.category not in prefs_by_cat:
                prefs_by_cat[p.category] = []
            prefs_by_cat[p.category].append(p.value)

        icon_map = {
            "cuisine": "🍽️ 美食偏好",
            "interest": "🏛️ 兴趣偏好",
            "pace": "👣 出行节奏",
            "budget_level": "💰 预算习惯",
            "companions": "👥 出行人数",
        }

        for category, icon_label in icon_map.items():
            if category in prefs_by_cat:
                values = "、".join(prefs_by_cat[category][:3])
                lines.append(f"{icon_label}: {values}")

        # Travel history
        if profile.travel_history:
            history_lines = []
            for r in profile.travel_history[:5]:
                days = f"{r.duration_days}天" if r.duration_days else ""
                entry = f"  · {r.destination}"
                if days:
                    entry += f" ({days})"
                if r.start_date:
                    entry += f" {r.start_date[:10]}"
                history_lines.append(entry)
            if history_lines:
                lines.append("📅 历史行程:")
                lines.extend(history_lines[:3])

        lines.append("===================\n")
        return "\n".join(lines)

    # ── Saving ──

    def save_from_result(self, intent, plan) -> None:
        """Save preferences and travel history from a completed planning result.

        Args:
            intent: TravelIntent from the Coordinator.
            plan: TravelPlan from the Planner.
        """
        if not intent or not plan:
            return

        # Learn preferences
        self.learner.learn_from_interaction(intent, plan)

        # Save travel record
        record = TravelRecord(
            destination=intent.destination or plan.destination or "",
            start_date=str(intent.start_date) if intent.start_date else None,
            duration_days=intent.duration_days or len(plan.days),
            companions=intent.companions or 1,
            budget_total=plan.budget_breakdown.total_estimated if plan.budget_breakdown else 0,
            interests=[c.value for c in intent.preferences.interests] if intent.preferences else [],
        )
        self.store.save_travel_record(record)

    # ── Utility ──

    def clear(self):
        """Clear all stored memory (for testing)."""
        self.store.clear_all()
