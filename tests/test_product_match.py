"""Product listing match: required groups + excludes."""

import pytest

from orchestrator.config_parser import parse_interface_config
from scrapers.keyword_engine import matches_from_match_dict, matches_keywords
from scrapers.product_match import explain_match, listing_matches, rules_from_dict


def test_etb_chaos_rising_vs_elite_trainer_box_title() -> None:
    rules = rules_from_dict(
        {
            "required_groups": [
                ["etb", "elite trainer box"],
                ["chaos rising"],
            ],
        }
    )
    assert listing_matches("Elite Trainer Box — Chaos Rising", rules)
    assert listing_matches("Pokemon ETB Chaos Rising", rules)


def test_etb_wrong_set_rejected() -> None:
    rules = rules_from_dict(
        {
            "required_groups": [
                ["etb", "elite trainer box"],
                ["chaos rising"],
            ],
        }
    )
    assert not listing_matches("ETB Ascended Heroes", rules)


def test_exclude_phrase_vetoes() -> None:
    rules = rules_from_dict(
        {
            "required_groups": [["etb"], ["chaos rising"]],
            "exclude": ["ascended heroes"],
        }
    )
    assert not listing_matches("ETB Chaos Rising Ascended Heroes Bundle", rules)


def test_explain_match_failed_group() -> None:
    rules = rules_from_dict({"required_groups": [["etb"], ["chaos rising"]]})
    exp = explain_match("ETB Ascended Heroes", rules)
    assert not exp.matches
    assert exp.failed_group_index == 1
    assert exp.excluded_by is None


def test_matches_keywords_backward_compat() -> None:
    assert matches_keywords(
        "ETB Chaos Rising Elite Trainer",
        [["etb"], ["chaos"]],
    )


def test_matches_from_match_dict() -> None:
    m = {"required_groups": [["elite trainer box"], ["chaos rising"]]}
    assert matches_from_match_dict("Elite Trainer Box Chaos Rising", m)


def test_parse_interface_config_normalizes_products() -> None:
    raw = {
        "products": [
            {
                "display_name": "x",
                "match": {
                    "required_groups": [["a", "b"], ["c"]],
                    "exclude": ["bad"],
                },
            }
        ]
    }
    out = parse_interface_config(raw)
    assert out["products"][0]["match"] == {
        "required_groups": [["a", "b"], ["c"]],
        "exclude": ["bad"],
    }


def test_rules_from_dict_rejects_empty_group() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        rules_from_dict({"required_groups": [["a"], []]})
