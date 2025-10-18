"""
SQLite helper for Editorium Bot V2.0 profiles & premium management.
Uses standard library sqlite3 so no extra runtime deps are required for DB operations.
This module provides a small, safe wrapper around SQLite with JSON storage for
arrays (portfolio links) and unix timestamps for datetimes.

API (sync):
- init_db(db_path)
- add_or_update_profile(db_path, profile_dict)
- get_profile(db_path, user_id)
- delete_profile(db_path, user_id)
- bump_profile(db_path, user_id, now_ts)
- set_config(db_path, guild_id, profile_channel_id)
- get_config(db_path, guild_id)
- add_premium(db_path, user_id, expiry_ts)
- remove_premium(db_path, user_id)
- list_active_premium(db_path, now_ts)
- is_premium(db_path, user_id, now_ts)

Note: All datetimes are stored as integer UNIX timestamps (seconds).
"""
from __future__ import annotations
import sqlite3
import json
import threading
import time
from typing import Optional, List, Dict, Any

_LOCK = threading.Lock()

_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS profiles (
    user_id TEXT PRIMARY KEY,
    bio TEXT,
    specialty TEXT,
    software TEXT,
    portfolio_links TEXT, -- JSON array
    banner_url TEXT,
    last_bump_time INTEGER,
    showcase_message_id TEXT,
    created_at INTEGER,
    rating_avg REAL DEFAULT 0.0,
    rating_count INTEGER DEFAULT 0,
    jobs_completed INTEGER DEFAULT 0,
    jobs_applied INTEGER DEFAULT 0,
    collabs_completed INTEGER DEFAULT 0,
    youtube_url TEXT,
    twitch_url TEXT,
    instagram_url TEXT,
    tiktok_url TEXT,
    twitter_url TEXT,
    verified_creator INTEGER DEFAULT 0,
    custom_theme TEXT -- JSON for premium themes
);

CREATE TABLE IF NOT EXISTS premium (
    user_id TEXT PRIMARY KEY,
    tier TEXT DEFAULT 'basic', -- basic, pro, elite
    expiry_date INTEGER
);

CREATE TABLE IF NOT EXISTS config (
    guild_id TEXT PRIMARY KEY,
    profile_channel_id TEXT,
    jobs_channel_id TEXT,
    logs_channel_id TEXT,
    reviews_channel_id TEXT,
    collab_channel_id TEXT,
    challenges_channel_id TEXT,
    available_job_roles TEXT -- JSON array
);

CREATE TABLE IF NOT EXISTS gamification (
    user_id TEXT PRIMARY KEY,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    points INTEGER DEFAULT 0,
    badges TEXT, -- JSON array of badge IDs
    achievements TEXT -- JSON array of achievement IDs
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    creator_id TEXT,
    guild_id TEXT,
    title TEXT,
    description TEXT,
    budget TEXT,
    software_required TEXT,
    deadline TEXT,
    reference_links TEXT,
    status TEXT DEFAULT 'open', -- open, in_progress, completed, closed
    created_at INTEGER,
    message_id TEXT,
    assigned_to TEXT
);

CREATE TABLE IF NOT EXISTS applications (
    application_id TEXT PRIMARY KEY,
    job_id TEXT,
    applicant_id TEXT,
    message TEXT,
    portfolio_links TEXT, -- JSON
    status TEXT DEFAULT 'pending', -- pending, accepted, rejected
    applied_at INTEGER,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);

CREATE TABLE IF NOT EXISTS ratings (
    rating_id TEXT PRIMARY KEY,
    reviewer_id TEXT,
    reviewee_id TEXT,
    job_id TEXT,
    rating INTEGER, -- 1-5
    comment TEXT,
    created_at INTEGER
);

CREATE TABLE IF NOT EXISTS collaborations (
    collab_id TEXT PRIMARY KEY,
    creator_id TEXT,
    title TEXT,
    description TEXT,
    roles_needed TEXT, -- JSON array
    status TEXT DEFAULT 'open',
    created_at INTEGER,
    participants TEXT -- JSON array of user_ids
);

CREATE TABLE IF NOT EXISTS marketplace_listings (
    listing_id TEXT PRIMARY KEY,
    seller_id TEXT,
    title TEXT,
    description TEXT,
    price REAL,
    category TEXT,
    status TEXT DEFAULT 'active',
    created_at INTEGER
);

CREATE TABLE IF NOT EXISTS follows (
    follower_id TEXT,
    following_id TEXT,
    followed_at INTEGER,
    PRIMARY KEY (follower_id, following_id)
);

CREATE TABLE IF NOT EXISTS challenges (
    challenge_id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    prize TEXT,
    deadline INTEGER,
    created_at INTEGER,
    status TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS challenge_submissions (
    submission_id TEXT PRIMARY KEY,
    challenge_id TEXT,
    user_id TEXT,
    submission_url TEXT,
    submitted_at INTEGER,
    votes INTEGER DEFAULT 0,
    FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id)
);

CREATE TABLE IF NOT EXISTS referrals (
    referrer_id TEXT,
    referred_id TEXT,
    referred_at INTEGER,
    reward_claimed INTEGER DEFAULT 0,
    PRIMARY KEY (referrer_id, referred_id)
);

CREATE TABLE IF NOT EXISTS leaderboard_cache (
    period TEXT, -- weekly, monthly, all_time
    category TEXT, -- jobs, ratings, xp
    data TEXT, -- JSON of top users
    last_updated INTEGER,
    PRIMARY KEY (period, category)
);

CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    leader_id TEXT NOT NULL,
    created_at INTEGER,
    max_members INTEGER DEFAULT 10,
    is_recruiting INTEGER DEFAULT 1,
    team_banner TEXT,
    team_website TEXT,
    team_social_links TEXT -- JSON object with social media links
);

CREATE TABLE IF NOT EXISTS team_members (
    team_id TEXT,
    user_id TEXT,
    role TEXT DEFAULT 'member', -- leader, admin, member
    joined_at INTEGER,
    invited_by TEXT,
    PRIMARY KEY (team_id, user_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS team_invites (
    invite_id TEXT PRIMARY KEY,
    team_id TEXT,
    invited_user_id TEXT,
    invited_by TEXT,
    status TEXT DEFAULT 'pending', -- pending, accepted, declined, expired
    created_at INTEGER,
    expires_at INTEGER,
    message TEXT,
    FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_premium_expiry ON premium(expiry_date);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_ratings_reviewee ON ratings(reviewee_id);
CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user ON team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_team_invites_user ON team_invites(invited_user_id);
"""


def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.executescript(_SCHEMA)
            conn.commit()
        finally:
            conn.close()


def add_or_update_profile(db_path: str, profile: Dict[str, Any]) -> None:
    """Insert or update a profile. profile is a dict with keys matching columns.
    portfolio_links should be a list; will be stored as JSON string.
    """
    user_id = str(profile["user_id"])
    bio = profile.get("bio")
    specialty = profile.get("specialty")
    software = profile.get("software")
    portfolio_links = json.dumps(profile.get("portfolio_links", []))
    banner_url = profile.get("banner_url")
    last_bump_time = profile.get("last_bump_time")
    showcase_message_id = profile.get("showcase_message_id")

    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO profiles (user_id, bio, specialty, software, portfolio_links, banner_url, last_bump_time, showcase_message_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    bio=excluded.bio,
                    specialty=excluded.specialty,
                    software=excluded.software,
                    portfolio_links=excluded.portfolio_links,
                    banner_url=excluded.banner_url,
                    last_bump_time=excluded.last_bump_time,
                    showcase_message_id=excluded.showcase_message_id
                """,
                (user_id, bio, specialty, software, portfolio_links, banner_url, last_bump_time, showcase_message_id),
            )
            conn.commit()
        finally:
            conn.close()


def get_profile(db_path: str, user_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM profiles WHERE user_id = ?", (str(user_id),))
            row = cur.fetchone()
            if not row:
                return None
            data = dict(row)
            # parse JSON
            try:
                data["portfolio_links"] = json.loads(data.get("portfolio_links") or "[]")
            except Exception:
                data["portfolio_links"] = []
            return data
        finally:
            conn.close()


def delete_profile(db_path: str, user_id: str) -> None:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM profiles WHERE user_id = ?", (str(user_id),))
            conn.commit()
        finally:
            conn.close()


def bump_profile(db_path: str, user_id: str, now_ts: Optional[int] = None) -> None:
    now_ts = int(now_ts or time.time())
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("UPDATE profiles SET last_bump_time = ? WHERE user_id = ?", (now_ts, str(user_id)))
            conn.commit()
        finally:
            conn.close()


def set_showcase_message_id(db_path: str, user_id: str, message_id: Optional[str]) -> None:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("UPDATE profiles SET showcase_message_id = ? WHERE user_id = ?", (message_id, str(user_id)))
            conn.commit()
        finally:
            conn.close()


def get_showcase_message_id(db_path: str, user_id: str) -> Optional[str]:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT showcase_message_id FROM profiles WHERE user_id = ?", (str(user_id),))
            row = cur.fetchone()
            if not row:
                return None
            return row["showcase_message_id"]
        finally:
            conn.close()


# Config helpers
def set_config(db_path: str, guild_id: str, config_data: Union[str, Dict[str, Any], None]) -> None:
    """Set config data for a guild. Can accept a single channel ID or a dict of config values."""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()

            if isinstance(config_data, dict):
                # Handle dictionary of config values
                cur.execute(
                    "INSERT INTO config (guild_id, profile_channel_id, jobs_channel_id, logs_channel_id, reviews_channel_id, collab_channel_id, challenges_channel_id, available_job_roles) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(guild_id) DO UPDATE SET profile_channel_id=excluded.profile_channel_id, jobs_channel_id=excluded.jobs_channel_id, logs_channel_id=excluded.logs_channel_id, reviews_channel_id=excluded.reviews_channel_id, collab_channel_id=excluded.collab_channel_id, challenges_channel_id=excluded.challenges_channel_id, available_job_roles=excluded.available_job_roles",
                    (
                        str(guild_id),
                        config_data.get('profile_channel_id'),
                        config_data.get('jobs_channel_id'),
                        config_data.get('logs_channel_id'),
                        config_data.get('reviews_channel_id'),
                        config_data.get('collab_channel_id'),
                        config_data.get('challenges_channel_id'),
                        config_data.get('available_job_roles')
                    ),
                )
            else:
                # Handle single profile_channel_id (backward compatibility)
                cur.execute(
                    "INSERT INTO config (guild_id, profile_channel_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET profile_channel_id=excluded.profile_channel_id",
                    (str(guild_id), config_data),
                )

            conn.commit()
        finally:
            conn.close()


def get_config(db_path: str, guild_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM config WHERE guild_id = ?", (str(guild_id),))
            row = cur.fetchone()
            if not row:
                return None
            return dict(row)
        finally:
            conn.close()


# Premium helpers
def add_premium(db_path: str, user_id: str, expiry_ts: int, tier: str = 'basic') -> None:
    """Add or update premium subscription with tier"""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO premium (user_id, tier, expiry_date) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET tier=excluded.tier, expiry_date=excluded.expiry_date",
                (str(user_id), tier, int(expiry_ts)),
            )
            conn.commit()
        finally:
            conn.close()


def remove_premium(db_path: str, user_id: str) -> None:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM premium WHERE user_id = ?", (str(user_id),))
            conn.commit()
        finally:
            conn.close()


def list_active_premium(db_path: str, now_ts: Optional[int] = None) -> List[Dict[str, Any]]:
    now_ts = int(now_ts or time.time())
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT user_id, expiry_date FROM premium WHERE expiry_date > ? ORDER BY expiry_date ASC", (now_ts,))
            rows = cur.fetchall()
            return [{"user_id": r["user_id"], "expiry_date": r["expiry_date"]} for r in rows]
        finally:
            conn.close()


def is_premium(db_path: str, user_id: str, now_ts: Optional[int] = None) -> bool:
    now_ts = int(now_ts or time.time())
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT expiry_date FROM premium WHERE user_id = ?", (str(user_id),))
            row = cur.fetchone()
            if not row:
                return False
            return int(row["expiry_date"]) > now_ts
        finally:
            conn.close()


# Team helpers
def create_team(db_path: str, team_id: str, name: str, description: str, leader_id: str, max_members: int = 10) -> None:
    """Create a new team"""
    now_ts = int(time.time())
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO teams (team_id, name, description, leader_id, created_at, max_members) VALUES (?, ?, ?, ?, ?, ?)",
                (team_id, name, description, str(leader_id), now_ts, max_members),
            )
            # Add leader as first member
            cur.execute(
                "INSERT INTO team_members (team_id, user_id, role, joined_at) VALUES (?, ?, 'leader', ?)",
                (team_id, str(leader_id), now_ts),
            )
            conn.commit()
        finally:
            conn.close()


def get_team(db_path: str, team_id: str) -> Optional[Dict[str, Any]]:
    """Get team information"""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM teams WHERE team_id = ?", (team_id,))
            row = cur.fetchone()
            if not row:
                return None
            data = dict(row)
            # Parse JSON social links
            try:
                data["team_social_links"] = json.loads(data.get("team_social_links") or "{}")
            except Exception:
                data["team_social_links"] = {}
            return data
        finally:
            conn.close()


def get_user_team(db_path: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Get the team a user belongs to"""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT t.*, tm.role FROM teams t
                JOIN team_members tm ON t.team_id = tm.team_id
                WHERE tm.user_id = ?
            """, (str(user_id),))
            row = cur.fetchone()
            if not row:
                return None
            data = dict(row)
            # Parse JSON social links
            try:
                data["team_social_links"] = json.loads(data.get("team_social_links") or "{}")
            except Exception:
                data["team_social_links"] = {}
            return data
        finally:
            conn.close()


def get_team_members(db_path: str, team_id: str) -> List[Dict[str, Any]]:
    """Get all members of a team"""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT tm.user_id, tm.role, tm.joined_at, tm.invited_by, p.bio, p.specialty
                FROM team_members tm
                LEFT JOIN profiles p ON tm.user_id = p.user_id
                WHERE tm.team_id = ?
                ORDER BY tm.joined_at ASC
            """, (team_id,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()


def add_team_member(db_path: str, team_id: str, user_id: str, invited_by: str, role: str = 'member') -> None:
    """Add a member to a team"""
    now_ts = int(time.time())
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO team_members (team_id, user_id, role, joined_at, invited_by) VALUES (?, ?, ?, ?, ?)",
                (team_id, str(user_id), role, now_ts, str(invited_by)),
            )
            conn.commit()
        finally:
            conn.close()


def remove_team_member(db_path: str, team_id: str, user_id: str) -> None:
    """Remove a member from a team"""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM team_members WHERE team_id = ? AND user_id = ?", (team_id, str(user_id)))
            conn.commit()
        finally:
            conn.close()


def update_team_member_role(db_path: str, team_id: str, user_id: str, role: str) -> None:
    """Update a team member's role"""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("UPDATE team_members SET role = ? WHERE team_id = ? AND user_id = ?", (role, team_id, str(user_id)))
            conn.commit()
        finally:
            conn.close()


def create_team_invite(db_path: str, invite_id: str, team_id: str, invited_user_id: str, invited_by: str, message: str = "", expires_hours: int = 48) -> None:
    """Create a team invitation"""
    now_ts = int(time.time())
    expires_at = now_ts + (expires_hours * 3600)
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO team_invites (invite_id, team_id, invited_user_id, invited_by, created_at, expires_at, message) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (invite_id, team_id, str(invited_user_id), str(invited_by), now_ts, expires_at, message),
            )
            conn.commit()
        finally:
            conn.close()


def get_team_invite(db_path: str, invite_id: str) -> Optional[Dict[str, Any]]:
    """Get team invitation details"""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM team_invites WHERE invite_id = ?", (invite_id,))
            row = cur.fetchone()
            if not row:
                return None
            return dict(row)
        finally:
            conn.close()


def accept_team_invite(db_path: str, invite_id: str) -> bool:
    """Accept a team invitation"""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            # Get invite details
            cur.execute("SELECT * FROM team_invites WHERE invite_id = ? AND status = 'pending'", (invite_id,))
            invite = cur.fetchone()
            if not invite:
                return False

            # Check if invite is expired
            now_ts = int(time.time())
            if invite["expires_at"] < now_ts:
                cur.execute("UPDATE team_invites SET status = 'expired' WHERE invite_id = ?", (invite_id,))
                conn.commit()
                return False

            # Check if user is already in a team
            cur.execute("SELECT team_id FROM team_members WHERE user_id = ?", (invite["invited_user_id"],))
            if cur.fetchone():
                return False

            # Check team member limit
            cur.execute("SELECT COUNT(*) as member_count, max_members FROM teams t JOIN team_members tm ON t.team_id = tm.team_id WHERE t.team_id = ?", (invite["team_id"],))
            team_info = cur.fetchone()
            if team_info and team_info["member_count"] >= team_info["max_members"]:
                return False

            # Add member to team
            cur.execute(
                "INSERT INTO team_members (team_id, user_id, role, joined_at, invited_by) VALUES (?, ?, 'member', ?, ?)",
                (invite["team_id"], invite["invited_user_id"], now_ts, invite["invited_by"]),
            )

            # Update invite status
            cur.execute("UPDATE team_invites SET status = 'accepted' WHERE invite_id = ?", (invite_id,))
            conn.commit()
            return True
        finally:
            conn.close()


def decline_team_invite(db_path: str, invite_id: str) -> bool:
    """Decline a team invitation"""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("UPDATE team_invites SET status = 'declined' WHERE invite_id = ? AND status = 'pending'", (invite_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


def update_team_settings(db_path: str, team_id: str, updates: Dict[str, Any]) -> None:
    """Update team settings"""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            set_parts = []
            values = []
            for key, value in updates.items():
                if key in ['name', 'description', 'max_members', 'is_recruiting', 'team_banner', 'team_website', 'team_social_links']:
                    set_parts.append(f"{key} = ?")
                    if key == 'team_social_links':
                        values.append(json.dumps(value))
                    else:
                        values.append(value)
            if set_parts:
                query = f"UPDATE teams SET {', '.join(set_parts)} WHERE team_id = ?"
                values.append(team_id)
                cur.execute(query, values)
                conn.commit()
        finally:
            conn.close()


def search_teams(db_path: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search teams by name or description"""
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            search_term = f"%{query}%"
            cur.execute("""
                SELECT t.*, COUNT(tm.user_id) as member_count
                FROM teams t
                LEFT JOIN team_members tm ON t.team_id = tm.team_id
                WHERE (t.name LIKE ? OR t.description LIKE ?) AND t.is_recruiting = 1
                GROUP BY t.team_id
                ORDER BY member_count DESC, t.created_at DESC
                LIMIT ?
            """, (search_term, search_term, limit))
            rows = cur.fetchall()
            teams = []
            for row in rows:
                team_data = dict(row)
                try:
                    team_data["team_social_links"] = json.loads(team_data.get("team_social_links") or "{}")
                except Exception:
                    team_data["team_social_links"] = {}
                teams.append(team_data)
            return teams
        finally:
            conn.close()
