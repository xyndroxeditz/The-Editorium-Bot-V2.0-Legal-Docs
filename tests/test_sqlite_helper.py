import os
import tempfile
import time
from db.sqlite_helper import init_db, add_or_update_profile, get_profile, is_premium, add_premium, list_active_premium, delete_profile


def test_profile_lifecycle():
    fd, path = tempfile.mkstemp(prefix="editorium_test_", suffix=".db")
    os.close(fd)
    try:
        init_db(path)
        profile = {
            "user_id": "12345",
            "bio": "Test bio",
            "specialty": "Editor",
            "software": "Premiere",
            "portfolio_links": ["https://example.com"],
            "banner_url": None,
            "last_bump_time": None,
        }
        add_or_update_profile(path, profile)
        p = get_profile(path, "12345")
        assert p is not None
        assert p["bio"] == "Test bio"
        # premium
        assert not is_premium(path, "12345")
        add_premium(path, "12345", int(time.time()) + 3600)
        assert is_premium(path, "12345")
        lst = list_active_premium(path)
        assert any(r["user_id"] == "12345" for r in lst)
        delete_profile(path, "12345")
        assert get_profile(path, "12345") is None
    finally:
        os.remove(path)
