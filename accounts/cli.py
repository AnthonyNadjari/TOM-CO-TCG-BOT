"""CLI: registry DB + cookie paths + manual Fnac session capture.

Examples::

  python -m accounts.cli init
  python -m accounts.cli add --site fnac --label work --email you@yourdomain.com
  python -m accounts.cli capture-fnac --cookie-label work
  python -m accounts.cli list --site fnac
  python -m accounts.cli status --label work
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path

from accounts.cookie_store import CookieStore
from accounts.fnac_session import capture_fnac_session_after_manual_login
from accounts.session_store import SessionStore


def _store(args: argparse.Namespace) -> SessionStore:
    return SessionStore(Path(args.db))


def _cookies(args: argparse.Namespace) -> CookieStore:
    return CookieStore(str(Path(args.cookies_dir)))


def cmd_init(args: argparse.Namespace) -> int:
    s = _store(args)
    s.init_schema()
    print(f"Initialized {s.db_path.resolve()}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    s = _store(args)
    s.init_schema()
    password = args.password
    if password is None and not args.no_password:
        password = getpass("Password (empty to skip): ") or None
    addr = None
    if args.address_json:
        addr = json.loads(Path(args.address_json).read_text(encoding="utf-8"))
    aid = s.add_account(
        site_id=args.site,
        label=args.label,
        email=args.email,
        username=args.username,
        password=password,
        address_snapshot=addr,
        notes=args.notes,
        cookie_label=args.cookie_label,
    )
    print(f"Added account id={aid} label={args.label!r} cookie_label={args.cookie_label or args.label!r}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    s = _store(args)
    s.init_schema()
    rows = s.list_by_site(args.site) if args.site else list(s.iter_all())
    for a in rows:
        print(
            f"{a.label}\t{a.email}\t{a.cookie_label}\t{a.session_status}\t{a.last_session_at or '-'}"
        )
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    s = _store(args)
    a = s.get_by_label(args.label)
    if not a:
        print("Unknown label", file=sys.stderr)
        return 1
    print(json.dumps(_account_public_dict(a), indent=2, ensure_ascii=False))
    return 0


def _account_public_dict(a) -> dict:
    return {
        "id": a.id,
        "site_id": a.site_id,
        "label": a.label,
        "email": a.email,
        "username": a.username,
        "password": a.password,
        "address_snapshot": a.address_snapshot,
        "notes": a.notes,
        "cookie_label": a.cookie_label,
        "last_session_at": a.last_session_at,
        "session_status": a.session_status,
    }


def cmd_status(args: argparse.Namespace) -> int:
    s = _store(args)
    c = _cookies(args)
    a = s.get_by_label(args.label)
    if not a:
        print("Unknown label", file=sys.stderr)
        return 1
    p = c.path_for(a.cookie_label)
    mtime = None
    if p.is_file():
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
    print(
        json.dumps(
            {
                "account": _account_public_dict(a),
                "cookie_file": str(p),
                "cookie_file_exists": p.is_file(),
                "cookie_file_mtime_utc": mtime,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_cookies_path(args: argparse.Namespace) -> int:
    s = _store(args)
    c = _cookies(args)
    a = s.get_by_label(args.label)
    if not a:
        print("Unknown label", file=sys.stderr)
        return 1
    print(c.path_for(a.cookie_label))
    return 0


def cmd_mark_stale(args: argparse.Namespace) -> int:
    s = _store(args)
    s.init_schema()
    n = s.mark_stale(args.site)
    print(f"Marked stale: {n} row(s)")
    return 0


def cmd_export_emails(args: argparse.Namespace) -> int:
    s = _store(args)
    s.init_schema()
    rows = s.list_by_site(args.site) if args.site else list(s.iter_all())
    out = [{"label": a.label, "email": a.email, "site_id": a.site_id} for a in rows]
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_capture_fnac(args: argparse.Namespace) -> int:
    s = _store(args)
    s.init_schema()
    c = _cookies(args)
    label = args.cookie_label
    if args.label:
        a = s.get_by_label(args.label)
        if not a:
            print("Unknown account label", file=sys.stderr)
            return 1
        if a.site_id != "fnac":
            print("Account is not fnac site_id", file=sys.stderr)
            return 1
        label = a.cookie_label
    capture_fnac_session_after_manual_login(
        cookie_label=label,
        cookie_store=c,
        session_store=s,
        login_url=args.login_url,
        start_path=args.warm_path,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Account registry and Fnac cookie capture")
    p.add_argument("--db", default="./data/accounts.sqlite3", help="SQLite path")
    p.add_argument("--cookies-dir", default="./data/cookies", help="Cookie JSON directory")

    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="Create database tables")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("add", help="Register an account row (credentials stay local under data/)")
    sp.add_argument("--site", required=True)
    sp.add_argument("--label", required=True)
    sp.add_argument("--email", required=True)
    sp.add_argument("--username", default=None)
    sp.add_argument("--password", default=None)
    sp.add_argument("--no-password", action="store_true")
    sp.add_argument("--cookie-label", default=None, help="Defaults to --label")
    sp.add_argument("--notes", default=None)
    sp.add_argument("--address-json", default=None, help="Path to JSON address snapshot")
    sp.set_defaults(func=cmd_add)

    sp = sub.add_parser("list", help="List accounts")
    sp.add_argument("--site", default=None)
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("show", help="Print one account as JSON")
    sp.add_argument("--label", required=True)
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("status", help="Account + cookie file freshness")
    sp.add_argument("--label", required=True)
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("cookies-path", help="Print absolute path to cookie JSON for an account")
    sp.add_argument("--label", required=True)
    sp.set_defaults(func=cmd_cookies_path)

    sp = sub.add_parser("mark-stale", help="Set session_status=stale (optionally per site)")
    sp.add_argument("--site", default=None)
    sp.set_defaults(func=cmd_mark_stale)

    sp = sub.add_parser("export-emails", help="JSON list of label/email/site")
    sp.add_argument("--site", default=None)
    sp.set_defaults(func=cmd_export_emails)

    sp = sub.add_parser(
        "capture-fnac",
        help="Headed browser: you log in, then cookies are saved for --cookie-label or --label",
    )
    g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("--cookie-label", default=None)
    g.add_argument("--label", default=None, help="Registry account label (uses its cookie_label)")
    sp.add_argument("--login-url", default=None)
    sp.add_argument("--warm-path", default=None, help="After login, open this path on www.fnac.com")
    sp.set_defaults(func=cmd_capture_fnac)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
