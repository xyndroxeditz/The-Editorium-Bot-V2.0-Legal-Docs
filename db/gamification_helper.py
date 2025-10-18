"""
Gamification helper functions for XP, levels, badges, achievements, and leaderboards.
"""
from __future__ import annotations
import sqlite3
import json
import threading
from typing import Optional, List, Dict, Any
import time

_LOCK = threading.Lock()

def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# XP and Levels
XP_PER_LEVEL = 100  # Base XP needed for level 1->2
LEVEL_MULTIPLIER = 1.5  # Each level requires 1.5x more XP

def calculate_level(xp: int) -> int:
    """Calculate level from total XP"""
    level = 1
    xp_needed = XP_PER_LEVEL
    while xp >= xp_needed:
        xp -= xp_needed
        level += 1
        xp_needed = int(XP_PER_LEVEL * (LEVEL_MULTIPLIER ** (level - 1)))
    return level

def get_xp_for_next_level(current_xp: int) -> tuple[int, int]:
    """Returns (current_level, xp_needed_for_next)"""
    level = calculate_level(current_xp)
    xp_for_current = sum([int(XP_PER_LEVEL * (LEVEL_MULTIPLIER ** i)) for i in range(level - 1)])
    xp_for_next = int(XP_PER_LEVEL * (LEVEL_MULTIPLIER ** (level - 1)))
    return level, xp_for_next - (current_xp - xp_for_current)

def add_xp(db_path: str, user_id: str, amount: int) -> Dict[str, Any]:
    """Add XP and return updated stats with level-up info"""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT xp, level FROM gamification WHERE user_id = ?", (str(user_id),))
            row = cur.fetchone()
            if not row:
                cur.execute("INSERT INTO gamification (user_id, xp, level) VALUES (?, ?, ?)", (str(user_id), amount, 1))
                conn.commit()
                return {"xp": amount, "level": 1, "leveled_up": False}
            
            old_xp = row["xp"]
            old_level = calculate_level(old_xp)
            new_xp = old_xp + amount
            new_level = calculate_level(new_xp)
            
            cur.execute("UPDATE gamification SET xp = ?, level = ? WHERE user_id = ?", (new_xp, new_level, str(user_id)))
            conn.commit()
            
            return {
                "xp": new_xp,
                "level": new_level,
                "leveled_up": new_level > old_level,
                "old_level": old_level
            }
        finally:
            conn.close()

def get_user_stats(db_path: str, user_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM gamification WHERE user_id = ?", (str(user_id),))
            row = cur.fetchone()
            if not row:
                return None
            data = dict(row)
            data["badges"] = json.loads(data.get("badges") or "[]")
            data["achievements"] = json.loads(data.get("achievements") or "[]")
            return data
        finally:
            conn.close()

# Badges and Achievements
def award_badge(db_path: str, user_id: str, badge_id: str) -> None:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT badges FROM gamification WHERE user_id = ?", (str(user_id),))
            row = cur.fetchone()
            if not row:
                cur.execute("INSERT INTO gamification (user_id, badges) VALUES (?, ?)", (str(user_id), json.dumps([badge_id])))
            else:
                badges = json.loads(row["badges"] or "[]")
                if badge_id not in badges:
                    badges.append(badge_id)
                    cur.execute("UPDATE gamification SET badges = ? WHERE user_id = ?", (json.dumps(badges), str(user_id)))
            conn.commit()
        finally:
            conn.close()

def award_achievement(db_path: str, user_id: str, achievement_id: str) -> None:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT achievements FROM gamification WHERE user_id = ?", (str(user_id),))
            row = cur.fetchone()
            if not row:
                cur.execute("INSERT INTO gamification (user_id, achievements) VALUES (?, ?)", (str(user_id), json.dumps([achievement_id])))
            else:
                achievements = json.loads(row["achievements"] or "[]")
                if achievement_id not in achievements:
                    achievements.append(achievement_id)
                    cur.execute("UPDATE gamification SET achievements = ? WHERE user_id = ?", (json.dumps(achievements), str(user_id)))
            conn.commit()
        finally:
            conn.close()

# Leaderboards
def get_leaderboard(db_path: str, category: str = "xp", limit: int = 10) -> List[Dict[str, Any]]:
    """Get top users by category (xp, jobs_completed, rating_avg)"""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            if category == "xp":
                cur.execute("SELECT user_id, xp, level FROM gamification ORDER BY xp DESC LIMIT ?", (limit,))
            elif category == "jobs":
                cur.execute("SELECT user_id, jobs_completed FROM profiles ORDER BY jobs_completed DESC LIMIT ?", (limit,))
            elif category == "rating":
                cur.execute("SELECT user_id, rating_avg, rating_count FROM profiles WHERE rating_count > 0 ORDER BY rating_avg DESC LIMIT ?", (limit,))
            else:
                return []
            
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

def update_leaderboard_cache(db_path: str, period: str, category: str) -> None:
    """Update cached leaderboard data"""
    data = get_leaderboard(db_path, category, 50)
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO leaderboard_cache (period, category, data, last_updated) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(period, category) DO UPDATE SET data=excluded.data, last_updated=excluded.last_updated",
                (period, category, json.dumps(data), int(time.time()))
            )
            conn.commit()
        finally:
            conn.close()
