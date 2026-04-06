from pathlib import Path

from accounts.session_store import SessionStore


def test_session_store_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "a.sqlite3"
    s = SessionStore(db)
    s.init_schema()
    s.add_account(
        site_id="fnac",
        label="acc1",
        email="a@example.com",
        username="user_a",
        password="secret",
        cookie_label="fnac_acc1",
    )
    rows = s.list_by_site("fnac")
    assert len(rows) == 1
    assert rows[0].email == "a@example.com"
    assert rows[0].cookie_label == "fnac_acc1"
    assert s.touch_session_by_cookie_label("fnac_acc1")
    again = s.get_by_label("acc1")
    assert again is not None
    assert again.last_session_at is not None
    assert again.session_status == "ok"
