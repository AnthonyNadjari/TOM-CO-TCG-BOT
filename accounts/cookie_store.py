"""Load and save session cookies per account."""

from __future__ import annotations

import json
from pathlib import Path


class CookieStore:
    def __init__(self, base_path: str = "./data/cookies") -> None:
        self.base_path = Path(base_path)

    def _file(self, label: str) -> Path:
        return self.base_path / f"{label}.json"

    def save(self, label: str, cookies: list[dict]) -> None:
        path = self._file(label)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cookies), encoding="utf-8")

    def load(self, label: str) -> list[dict] | None:
        path = self._file(label)
        if not path.is_file():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return None
        return raw

    def path_for(self, label: str) -> Path:
        return self._file(label).resolve()

    def list_labels(self) -> list[str]:
        if not self.base_path.is_dir():
            return []
        return sorted(p.stem for p in self.base_path.glob("*.json") if p.is_file())
