"""User profile — persists user identity, preference tags, and travel history.

SQLite schema:
  - preferences: key-value pairs for learned preferences
  - travel_history: records of past trip plans
"""

import json
import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


# ── Pydantic models ──


class PreferenceEntry(BaseModel):
    """A single learned preference."""

    category: str = Field(..., description="Preference category, e.g. cuisine, interest, budget_level")
    value: str = Field(..., description="Preference value, e.g. 川菜, 博物馆, 舒适型")
    confidence: float = Field(default=1.0, ge=0, le=1, description="Confidence score (0-1)")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class TravelRecord(BaseModel):
    """A historical travel plan."""

    destination: str = Field(..., description="City visited")
    start_date: Optional[str] = Field(default=None)
    end_date: Optional[str] = Field(default=None)
    duration_days: Optional[int] = Field(default=None)
    companions: int = Field(default=1)
    budget_total: float = Field(default=0)
    interests: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class UserProfile(BaseModel):
    """Aggregated user profile built from stored data."""

    preferences: list[PreferenceEntry] = Field(default_factory=list)
    travel_history: list[TravelRecord] = Field(default_factory=list)
    total_trips: int = Field(default=0)
    frequent_destinations: list[str] = Field(default_factory=list)
    common_interests: list[str] = Field(default_factory=list)
    typical_companions: int = Field(default=1)

    @property
    def is_new_user(self) -> bool:
        return self.total_trips == 0


# ── Database layer ──

_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "travel_memory.db"


class UserProfileStore:
    """SQLite-backed user profile storage."""

    def __init__(self, db_path: str | Path = _DEFAULT_DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    # ── Schema init ──

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    updated_at TEXT NOT NULL,
                    UNIQUE(category, value)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS travel_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    destination TEXT NOT NULL,
                    start_date TEXT,
                    end_date TEXT,
                    duration_days INTEGER,
                    companions INTEGER DEFAULT 1,
                    budget_total REAL DEFAULT 0,
                    interests TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    # ── Preferences CRUD ──

    def save_preference(self, category: str, value: str, confidence: float = 1.0):
        """Upsert a preference entry."""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO preferences (category, value, confidence, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(category, value)
                DO UPDATE SET confidence = ?, updated_at = ?
            """, (category, value, confidence, now, confidence, now))
            conn.commit()

    def get_preferences(self, category: str | None = None) -> list[PreferenceEntry]:
        """Get preferences, optionally filtered by category."""
        with sqlite3.connect(self.db_path) as conn:
            if category:
                rows = conn.execute(
                    "SELECT category, value, confidence, updated_at FROM preferences WHERE category = ? ORDER BY confidence DESC",
                    (category,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT category, value, confidence, updated_at FROM preferences ORDER BY confidence DESC"
                ).fetchall()
        return [
            PreferenceEntry(category=r[0], value=r[1], confidence=r[2], updated_at=r[3])
            for r in rows
        ]

    # ── Travel history CRUD ──

    def save_travel_record(self, record: TravelRecord):
        """Insert a travel history record."""
        now = datetime.now().isoformat()
        interests_json = json.dumps(record.interests, ensure_ascii=False)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO travel_history
                   (destination, start_date, end_date, duration_days, companions, budget_total, interests, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (record.destination, record.start_date, record.end_date,
                 record.duration_days, record.companions, record.budget_total,
                 interests_json, now),
            )
            conn.commit()

    def get_travel_history(self, limit: int = 10) -> list[TravelRecord]:
        """Get most recent travel records."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT destination, start_date, end_date, duration_days, companions, budget_total, interests, created_at "
                "FROM travel_history ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            TravelRecord(
                destination=r[0], start_date=r[1], end_date=r[2],
                duration_days=r[3], companions=r[4], budget_total=r[5],
                interests=json.loads(r[6]) if r[6] else [],
                created_at=r[7],
            )
            for r in rows
        ]

    # ── Profile assembly ──

    def get_profile(self) -> UserProfile:
        """Assemble the full user profile from stored data."""
        prefs = self.get_preferences()
        history = self.get_travel_history(limit=20)

        # Compute aggregates
        dests = [r.destination for r in history if r.destination]
        dest_counts: dict[str, int] = {}
        for d in dests:
            dest_counts[d] = dest_counts.get(d, 0) + 1
        frequent = sorted(dest_counts, key=dest_counts.get, reverse=True)[:5]

        # Collect common interests from history
        all_interests: list[str] = []
        for r in history:
            all_interests.extend(r.interests)
        interest_counts: dict[str, int] = {}
        for i in all_interests:
            interest_counts[i] = interest_counts.get(i, 0) + 1
        common = [i for i, _ in sorted(interest_counts.items(), key=lambda x: x[1], reverse=True)][:5]

        # Typical companions (most recent mode)
        companions_list = [r.companions for r in history if r.companions > 0]
        typical = max(set(companions_list), key=companions_list.count) if companions_list else 1

        return UserProfile(
            preferences=prefs,
            travel_history=history[:5],
            total_trips=len(history),
            frequent_destinations=frequent,
            common_interests=common,
            typical_companions=typical,
        )

    def clear_all(self):
        """Clear all data (for testing)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM preferences")
            conn.execute("DELETE FROM travel_history")
            conn.commit()
