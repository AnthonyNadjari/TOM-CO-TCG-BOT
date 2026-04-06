"""Headed Playwright flow: manual Fnac login, then persist cookies for a registry label."""

from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import Browser, sync_playwright

from accounts.cookie_store import CookieStore
from accounts.session_store import SessionStore
from sites.fnac import config
from sites.fnac.playwright_fnac import _accept_cookies, _new_context

_LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
]


def capture_fnac_session_after_manual_login(
    *,
    cookie_label: str,
    cookie_store: CookieStore | None = None,
    session_store: SessionStore | None = None,
    user_agent: str | None = None,
    login_url: str | None = None,
    start_path: str | None = None,
) -> Path:
    """
    Opens a visible browser on Fnac login. You complete login (and any address setup) yourself,
    then press Enter in the terminal to save ``context.cookies()`` for ``cookie_label``.
    """
    ua = user_agent or config.DEFAULT_USER_AGENT
    url = login_url or config.FNAC_LOGIN_URL
    store = cookie_store or CookieStore()
    reg = session_store

    print(f"Browser opening: {url}")
    print("After you are logged in and the account looks good, return here and press Enter to save cookies.")
    if start_path:
        print(f"(Optional warm-up) storefront path after login: {start_path}")

    cookies: list[dict] = []
    out = store.path_for(cookie_label)
    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=False, args=_LAUNCH_ARGS)
        ctx = _new_context(browser, ua)
        raw = store.load(cookie_label)
        if raw:
            ctx.add_cookies(raw)
        page = ctx.new_page()
        try:
            page.goto(url, timeout=120_000, wait_until="domcontentloaded")
            _accept_cookies(page)
            input("Press Enter when logged in and ready to save cookies… ")
            if start_path:
                path = start_path if start_path.startswith("/") else f"/{start_path}"
                page.goto(f"{config.BASE_URL}{path}", timeout=120_000, wait_until="domcontentloaded")
                time.sleep(0.5)
            cookies = ctx.cookies()
            store.save(cookie_label, cookies)
            out = store.path_for(cookie_label)
            if reg:
                reg.touch_session_by_cookie_label(cookie_label, status="ok")
        finally:
            page.close()
            ctx.close()
            browser.close()

    print(f"Saved {len(cookies)} cookies to {out}")
    return out
