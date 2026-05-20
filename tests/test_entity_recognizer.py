"""Entity recognizer unit tests.

分兩組：
1. TestEntityMatchScore — 純邏輯，合成 entity list，不需要 spaCy。
2. TestExtractEntities  — 需要 spaCy + en_core_web_sm；模型不在則 skip。
3. TestFallback         — mock 掉 spaCy，驗證 graceful degradation。
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src import entity_recognizer


# ---------------------------------------------------------------------------
# 1. entity_match_score（純函式，不需 spaCy）
# ---------------------------------------------------------------------------

class TestEntityMatchScore:
    def test_empty_entities_returns_zero(self):
        cfg = {"entity_names": ["UN"], "entity_types": ["GPE"]}
        assert entity_recognizer.entity_match_score([], cfg) == 0.0

    def test_empty_config_returns_zero(self):
        ents = [{"text": "UN", "label": "ORG"}]
        assert entity_recognizer.entity_match_score(ents, {}) == 0.0

    def test_single_name_match_returns_half(self):
        ents = [{"text": "NATO", "label": "ORG"}]
        cfg = {"entity_names": ["NATO", "UN"], "entity_types": []}
        assert entity_recognizer.entity_match_score(ents, cfg) == 0.5

    def test_two_name_matches_returns_one(self):
        ents = [
            {"text": "NATO", "label": "ORG"},
            {"text": "UN", "label": "ORG"},
        ]
        cfg = {"entity_names": ["NATO", "UN"], "entity_types": []}
        assert entity_recognizer.entity_match_score(ents, cfg) == 1.0

    def test_type_match_two_gpe(self):
        ents = [
            {"text": "France", "label": "GPE"},
            {"text": "Germany", "label": "GPE"},
        ]
        cfg = {"entity_names": [], "entity_types": ["GPE"]}
        assert entity_recognizer.entity_match_score(ents, cfg) == 1.0

    def test_name_match_is_case_insensitive(self):
        ents = [{"text": "nato", "label": "ORG"}]
        cfg = {"entity_names": ["NATO"], "entity_types": []}
        assert entity_recognizer.entity_match_score(ents, cfg) == 0.5

    def test_duplicate_entity_counted_once(self):
        ents = [
            {"text": "NATO", "label": "ORG"},
            {"text": "NATO", "label": "ORG"},
        ]
        cfg = {"entity_names": ["NATO"], "entity_types": []}
        assert entity_recognizer.entity_match_score(ents, cfg) == 0.5

    def test_mixed_name_and_type_hits(self):
        ents = [
            {"text": "NATO", "label": "ORG"},
            {"text": "$5 billion", "label": "MONEY"},
        ]
        cfg = {"entity_names": ["NATO"], "entity_types": ["MONEY"]}
        assert entity_recognizer.entity_match_score(ents, cfg) == 1.0

    def test_no_match_returns_zero(self):
        ents = [{"text": "John", "label": "PERSON"}]
        cfg = {"entity_names": ["NATO"], "entity_types": ["GPE"]}
        assert entity_recognizer.entity_match_score(ents, cfg) == 0.0

    def test_three_or_more_hits_still_one(self):
        ents = [
            {"text": "NATO", "label": "ORG"},
            {"text": "UN", "label": "ORG"},
            {"text": "France", "label": "GPE"},
        ]
        cfg = {"entity_names": ["NATO", "UN"], "entity_types": ["GPE"]}
        assert entity_recognizer.entity_match_score(ents, cfg) == 1.0

    def test_name_takes_priority_over_type(self):
        """NATO is in entity_names — matched as name, not via ORG type."""
        ents = [{"text": "NATO", "label": "ORG"}]
        cfg = {"entity_names": ["NATO"], "entity_types": ["ORG"]}
        # Only 1 hit (name match), not 2
        assert entity_recognizer.entity_match_score(ents, cfg) == 0.5

    def test_money_and_percent_for_econ(self):
        ents = [
            {"text": "$2 trillion", "label": "MONEY"},
            {"text": "0.25%", "label": "PERCENT"},
        ]
        cfg = {"entity_names": [], "entity_types": ["MONEY", "PERCENT"]}
        assert entity_recognizer.entity_match_score(ents, cfg) == 1.0

    def test_work_of_art_for_arts(self):
        ents = [{"text": "Hamlet", "label": "WORK_OF_ART"}]
        cfg = {"entity_names": [], "entity_types": ["WORK_OF_ART"]}
        assert entity_recognizer.entity_match_score(ents, cfg) == 0.5


# ---------------------------------------------------------------------------
# 2. extract_entities（需要 spaCy + en_core_web_sm）
# ---------------------------------------------------------------------------

class TestExtractEntities:
    @pytest.fixture(autouse=True)
    def _require_spacy_model(self):
        spacy = pytest.importorskip("spacy")
        try:
            spacy.load("en_core_web_sm")
        except OSError:
            pytest.skip("en_core_web_sm model not installed")
        entity_recognizer.reset()
        yield
        entity_recognizer.reset()

    def test_extracts_org_or_gpe(self):
        ents = entity_recognizer.extract_entities(
            "NATO and the United Nations held a summit in Brussels."
        )
        labels = {e["label"] for e in ents}
        assert labels & {"ORG", "GPE"}, f"expected ORG/GPE, got {labels}"
        assert len(ents) >= 2

    def test_extracts_gpe_from_countries(self):
        ents = entity_recognizer.extract_entities(
            "France and Germany signed a treaty in Paris."
        )
        gpe = [e for e in ents if e["label"] == "GPE"]
        assert len(gpe) >= 2

    def test_extracts_money_or_percent(self):
        ents = entity_recognizer.extract_entities(
            "The Fed raised rates by 0.25%, affecting $2 trillion in bonds."
        )
        labels = {e["label"] for e in ents}
        assert labels & {"MONEY", "PERCENT"}, f"expected MONEY/PERCENT, got {labels}"

    def test_empty_text_returns_empty(self):
        assert entity_recognizer.extract_entities("") == []

    def test_returns_list_of_dicts_with_text_and_label(self):
        ents = entity_recognizer.extract_entities("OpenAI released GPT-5 today.")
        for e in ents:
            assert "text" in e
            assert "label" in e


# ---------------------------------------------------------------------------
# 3. Fallback（mock spaCy unavailable）
# ---------------------------------------------------------------------------

class TestFallback:
    def test_returns_empty_when_nlp_unavailable(self):
        with patch.object(entity_recognizer, "_load_nlp", return_value=None):
            result = entity_recognizer.extract_entities("NATO summit in France")
            assert result == []
