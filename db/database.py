import sqlite3
import json
from datetime import datetime, timezone
from config import DB_PATH


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER,
                height_cm REAL,
                weight_kg REAL,
                goals TEXT,
                gym_frequency TEXT,
                experience_level TEXT,
                injuries TEXT,
                diet_prefs TEXT,
                onboarding_complete INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS workout_log (
                id INTEGER PRIMARY KEY,
                date TEXT,
                description TEXT,
                logged_at TEXT
            );
        """)


def get_profile() -> dict | None:
    """Return the user profile as a dict, or None if not set up."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM user_profile WHERE id = 1"
        ).fetchone()
    if row is None:
        return None
    return dict(row)


def save_profile(data: dict) -> None:
    """Insert or replace the user profile (always id=1 for single-user MVP)."""
    now = datetime.now(timezone.utc).isoformat()
    existing = get_profile()
    with _connect() as conn:
        if existing is None:
            conn.execute(
                """INSERT INTO user_profile
                   (id, name, age, height_cm, weight_kg, goals, gym_frequency,
                    experience_level, injuries, diet_prefs, onboarding_complete,
                    created_at, updated_at)
                   VALUES (1, :name, :age, :height_cm, :weight_kg, :goals,
                           :gym_frequency, :experience_level, :injuries,
                           :diet_prefs, 1, :created_at, :updated_at)""",
                {**data, "created_at": now, "updated_at": now},
            )
        else:
            conn.execute(
                """UPDATE user_profile SET
                   name=:name, age=:age, height_cm=:height_cm,
                   weight_kg=:weight_kg, goals=:goals,
                   gym_frequency=:gym_frequency,
                   experience_level=:experience_level,
                   injuries=:injuries, diet_prefs=:diet_prefs,
                   onboarding_complete=1, updated_at=:updated_at
                   WHERE id = 1""",
                {**data, "updated_at": now},
            )


def format_profile(profile: dict) -> str:
    """Return a readable one-line summary of the profile for agent context."""
    if not profile:
        return "No profile available."
    return (
        f"Name: {profile.get('name', 'Unknown')}, "
        f"Age: {profile.get('age', '?')}, "
        f"Height: {profile.get('height_cm', '?')} cm, "
        f"Weight: {profile.get('weight_kg', '?')} kg, "
        f"Goals: {profile.get('goals', 'Not specified')}, "
        f"Gym frequency: {profile.get('gym_frequency', 'Not specified')}, "
        f"Experience: {profile.get('experience_level', 'Not specified')}, "
        f"Injuries/limitations: {profile.get('injuries', 'None')}, "
        f"Diet preferences: {profile.get('diet_prefs', 'None')}"
    )


def get_workouts(limit: int = 20) -> list[dict]:
    """Return recent workout log entries."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM workout_log ORDER BY logged_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def add_workout(description: str, date: str | None = None) -> None:
    """Log a workout entry."""
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO workout_log (date, description, logged_at) VALUES (?, ?, ?)",
            (date or now[:10], description, now),
        )
