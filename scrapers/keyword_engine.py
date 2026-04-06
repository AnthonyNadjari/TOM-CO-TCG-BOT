"""Match product titles against keyword groups (AND across groups, OR within each)."""

from __future__ import annotations

from scrapers.product_match import ProductMatchRules, listing_matches, rules_from_dict


def matches_keywords(
    text: str,
    required_groups: list[list[str]],
    exclude_phrases: list[str] | None = None,
) -> bool:
    """
    True if every group has at least one keyword substring in ``text`` (after normalization),
    and no exclude phrase appears.
    """
    rules = ProductMatchRules(
        required_groups=tuple(tuple(g) for g in required_groups),
        exclude_phrases=tuple(exclude_phrases or ()),
    )
    return listing_matches(text, rules)


def matches_from_match_dict(text: str, match: dict) -> bool:
    """Convenience: ``match`` is the same object as ``product["match"]`` from the API."""
    return listing_matches(text, rules_from_dict(match))
