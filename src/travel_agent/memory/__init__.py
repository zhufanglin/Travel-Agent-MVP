"""Memory module — persistent user preference and travel history storage.

MVP uses SQLite. No external database required.

Architecture:
  memory_manager.py  ←  Facade — used by adapter
      ├── user_profile.py   — UserProfile model + DB CRUD
      └── preference_store.py — Preference extraction + storage
"""
