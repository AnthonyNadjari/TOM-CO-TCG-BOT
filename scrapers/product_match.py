"""Structured listing match: AND across groups, OR inside each group, optional excludes."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MatchExplanation:
    matches: bool
    failed_group_index: int | None  # first group with no keyword hit; None if all matched
    excluded_by: str | None  # first exclude phrase that matched normalized title, or None


@dataclass(frozen=True)
class ProductMatchRules:
    """At least one normalized keyword from each group must appear in the title; excludes veto."""

    required_groups: tuple[tuple[str, ...], ...]
    exclude_phrases: tuple[str, ...] = ()


def normalize_text(text: str) -> str:
    """Lowercase, drop punctuation, collapse whitespace — for substring checks on titles."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def listing_matches(title: str, rules: ProductMatchRules) -> bool:
    return explain_match(title, rules).matches


def explain_match(title: str, rules: ProductMatchRules) -> MatchExplanation:
    norm = normalize_text(title)

    for ex in rules.exclude_phrases:
        ex_n = normalize_text(ex)
        if ex_n and ex_n in norm:
            return MatchExplanation(False, None, ex_n)

    for i, group in enumerate(rules.required_groups):
        if not group:
            return MatchExplanation(False, i, None)
        hit = False
        for kw in group:
            k = normalize_text(kw)
            if k and k in norm:
                hit = True
                break
        if not hit:
            return MatchExplanation(False, i, None)

    return MatchExplanation(True, None, None)


def rules_from_dict(data: dict) -> ProductMatchRules:
    """Build rules from ``match`` object or flat dict with ``required_groups``."""
    groups_raw = data.get("required_groups")
    if groups_raw is None:
        raise ValueError("required_groups is required")

    if not isinstance(groups_raw, list) or not groups_raw:
        raise ValueError("required_groups must be a non-empty list of lists")

    groups: list[tuple[str, ...]] = []
    for i, g in enumerate(groups_raw):
        if not isinstance(g, list) or not g:
            raise ValueError(f"required_groups[{i}] must be a non-empty list of strings")
        cleaned: list[str] = []
        for s in g:
            if not isinstance(s, str) or not s.strip():
                raise ValueError(f"required_groups[{i}] contains empty or non-string keyword")
            cleaned.append(s.strip())
        groups.append(tuple(cleaned))

    ex = data.get("exclude") or data.get("exclude_phrases") or []
    if ex is None:
        ex = []
    if not isinstance(ex, list):
        raise ValueError("exclude / exclude_phrases must be a list of strings")
    ex_t: list[str] = []
    for s in ex:
        if not isinstance(s, str) or not s.strip():
            raise ValueError("exclude list must contain non-empty strings")
        ex_t.append(s.strip())

    return ProductMatchRules(
        required_groups=tuple(groups),
        exclude_phrases=tuple(ex_t),
    )


def normalize_product_match_block(product: dict) -> dict:
    """
    Ensure ``product["match"]`` exists and is validated; same shape the interface should send.

    Accepts either ``{ "match": { ... } }`` or legacy ``{ "required_groups": ... }`` at top level.
    """
    out = dict(product)
    if "match" in out and isinstance(out["match"], dict):
        block = dict(out["match"])
    else:
        block = {k: out[k] for k in ("required_groups", "exclude", "exclude_phrases") if k in out}

    rules = rules_from_dict(block)
    out["match"] = {
        "required_groups": [list(g) for g in rules.required_groups],
        "exclude": list(rules.exclude_phrases),
    }
    return out
