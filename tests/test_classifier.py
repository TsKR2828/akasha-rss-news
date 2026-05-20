"""Phase 2 — classifier 單元測試。

對應規格 §6.1 / §6.2 與 §20.1 P0 / P1。

NOTE: 既有的測試用 ``_mock_ner`` fixture 把 entity extraction
      mock 為空 list，確保 entity_score = 0 → 既有數字不變。
      Entity 相關驗證集中在 TestEntityIntegration。
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src import classifier, entity_recognizer


BEATS_CONFIG = {
    "classification": {
        "source_default_weight": 0.6,
        "keyword_weight": 0.3,
        "entity_weight": 0.1,
        "min_score": 0.45,
    },
    "ai_exception_sources": ["the_verge", "bbc_technology", "ars_technica_ai"],
    "beats": {
        "INTL": {
            "keywords_en": ["war", "summit", "treaty", "sanctions"],
            "keywords_zh": ["戰爭", "峰會"],
            "entities": {
                "entity_names": ["UN", "NATO", "EU"],
                "entity_types": ["GPE"],
            },
        },
        "ARTS": {
            "keywords_en": ["pulitzer", "cannes", "exhibition"],
            "keywords_zh": ["影展", "展覽"],
            "entities": {
                "entity_names": ["MoMA", "Tate", "Louvre", "Grammy", "Oscar"],
                "entity_types": ["WORK_OF_ART"],
            },
        },
        "AI": {
            "keywords_en": ["ai", "gpt", "llm", "claude", "neural"],
            "keywords_zh": ["大模型"],
            "entities": {
                "entity_names": ["OpenAI", "Anthropic", "DeepMind"],
                "entity_types": [],
            },
        },
        "ECON": {
            "keywords_en": ["fed", "inflation", "tariff"],
            "keywords_zh": ["通膨"],
            "entities": {
                "entity_names": ["Federal Reserve", "ECB", "IMF"],
                "entity_types": ["MONEY", "PERCENT"],
            },
        },
    },
}


@pytest.fixture(autouse=True)
def _mock_ner():
    """所有既有測試 entity extraction = []，保持分數不變。"""
    with patch.object(entity_recognizer, "extract_entities", return_value=[]):
        yield


def _article(source_id: str = "bbc_world", beats: list[str] | None = None,
             title: str = "", summary: str = "", tier: int = 1) -> dict:
    # 注意：用 `is None` 區分「未傳」與「明確傳空 list」
    return {
        "article_id": "x" * 64,
        "source_id": source_id,
        "publisher": "BBC",
        "tier": tier,
        "beat_candidates": ["INTL"] if beats is None else beats,
        "title": title,
        "summary": summary,
        "url": "https://x.com/a",
        "canonical_url": "https://x.com/a",
        "published_at": "2026-05-18T01:20:00+08:00",
        "fetched_at": "2026-05-18T05:00:00+08:00",
        "lang": "en",
        "raw_hash": "y" * 64,
    }


class TestSourceDefault:
    def test_source_default_alone_passes_min_score(self):
        """source.beats=[INTL] → INTL 得 0.6，>0.45 → 通過分類。"""
        art = _article(beats=["INTL"], title="Random title", summary="...")
        primary, scores = classifier.classify(art, BEATS_CONFIG)
        assert primary == "INTL"
        assert scores["INTL"] == pytest.approx(0.6)

    def test_keyword_boosts_score(self):
        """命中 ≥2 個關鍵字 → keyword_score = 1.0 → 總分 0.6 + 0.3 = 0.9。"""
        art = _article(beats=["INTL"],
                       title="Major summit on war and sanctions",
                       summary="Treaty signed")
        primary, scores = classifier.classify(art, BEATS_CONFIG)
        assert primary == "INTL"
        assert scores["INTL"] == pytest.approx(0.9)


class TestAIException:
    def test_verge_without_ai_keyword_demoted(self):
        """§6.2: The Verge 沒 AI 關鍵字 → AI 得 0。"""
        art = _article(source_id="the_verge", beats=["AI"],
                       title="New iPhone released",
                       summary="Apple announced a new phone today.")
        primary, scores = classifier.classify(art, BEATS_CONFIG)
        assert scores.get("AI", 0) == 0.0
        # 沒其他 beat 也算 → primary 應為 None（全部 < 0.45）
        assert primary is None

    def test_verge_with_ai_keyword_kept(self):
        """The Verge 命中 AI 關鍵字 → 正常分類。"""
        art = _article(source_id="the_verge", beats=["AI"],
                       title="New GPT-5 model from OpenAI",
                       summary="LLM benchmark results.")
        primary, scores = classifier.classify(art, BEATS_CONFIG)
        assert primary == "AI"
        assert scores["AI"] >= 0.45

    def test_non_exception_source_with_ai_beat_kept_without_keyword(self):
        """非例外來源（例如 MarkTechPost）即使沒 AI 關鍵字，source default 仍給 0.6。"""
        art = _article(source_id="marktechpost", beats=["AI"],
                       title="Lorem ipsum",
                       summary="dolor sit amet")
        primary, scores = classifier.classify(art, BEATS_CONFIG)
        assert primary == "AI"


class TestPTSLocal:
    def test_pts_local_bypasses_min_score(self):
        """PTS_LOCAL 來源直接歸類，不參與一般 beat 競爭。"""
        art = _article(source_id="pts_news", beats=["PTS_LOCAL"],
                       title="台北市府公告", summary="...")
        primary, scores = classifier.classify(art, BEATS_CONFIG)
        assert primary == "PTS_LOCAL"


class TestMinScoreReject:
    def test_low_score_returns_none(self):
        """source.beats=[] → 0 from source, 0 from keywords → < 0.45 → None。"""
        art = _article(source_id="weird_source", beats=[],
                       title="Some article", summary="content")
        primary, scores = classifier.classify(art, BEATS_CONFIG)
        assert primary is None


class TestMultiBeatRanking:
    def test_picks_highest_score_when_multiple_candidates(self):
        """source.beats=[ECON, AI] 都得 0.6，但 ECON 多命中關鍵字 → primary=ECON。"""
        art = _article(source_id="reuters_business_google_news",
                       beats=["ECON", "AI"],
                       title="Fed raises rates amid inflation; tariff also up")
        primary, scores = classifier.classify(art, BEATS_CONFIG)
        assert primary == "ECON"
        assert scores["ECON"] > scores["AI"]


class TestClassifyArticleEnrichment:
    def test_returns_new_dict_with_beat_and_scores(self):
        art = _article(beats=["INTL"], title="summit and war")
        enriched = classifier.classify_article(art, BEATS_CONFIG)
        # 原物件未被改
        assert "beat" not in art
        # 新物件帶 beat / beat_scores
        assert enriched["beat"] == "INTL"
        assert "INTL" in enriched["beat_scores"]


# ---------------------------------------------------------------------------
# Entity integration — 覆寫 autouse _mock_ner，注入合成 entity list
# ---------------------------------------------------------------------------

class TestEntityIntegration:
    """驗證 entity_score 確實影響最終分數。"""

    def test_entity_adds_0_1_when_two_hits(self, _mock_ner):
        """source(0.6) + keyword(0) + entity(1.0*0.1) = 0.7。"""
        fake_entities = [
            {"text": "France", "label": "GPE"},
            {"text": "Germany", "label": "GPE"},
        ]
        with patch.object(entity_recognizer, "extract_entities",
                          return_value=fake_entities):
            art = _article(beats=["INTL"], title="Random title", summary="...")
            primary, scores = classifier.classify(art, BEATS_CONFIG)
            assert primary == "INTL"
            assert scores["INTL"] == pytest.approx(0.7)

    def test_entity_adds_0_05_when_one_hit(self, _mock_ner):
        """source(0.6) + keyword(0) + entity(0.5*0.1) = 0.65。"""
        fake_entities = [{"text": "NATO", "label": "ORG"}]
        with patch.object(entity_recognizer, "extract_entities",
                          return_value=fake_entities):
            art = _article(beats=["INTL"], title="Random title", summary="...")
            primary, scores = classifier.classify(art, BEATS_CONFIG)
            assert scores["INTL"] == pytest.approx(0.65)

    def test_entity_zero_when_no_match(self, _mock_ner):
        """entities 都不命中 → entity_score=0 → 分數不變（同 MVP）。"""
        fake_entities = [{"text": "John", "label": "PERSON"}]
        with patch.object(entity_recognizer, "extract_entities",
                          return_value=fake_entities):
            art = _article(beats=["INTL"], title="Random title", summary="...")
            _, scores = classifier.classify(art, BEATS_CONFIG)
            assert scores["INTL"] == pytest.approx(0.6)

    def test_entity_helps_cross_min_score_threshold(self, _mock_ner):
        """source=0, keyword=1 hit(0.5) → kw=0.15 < 0.45。
        加上 entity 2 hits(1.0) → entity=0.10 → total=0.25 仍不過。
        但 source=1 + entity → 可過。"""
        # source=0 + keyword=0.15 + entity=0.10 = 0.25 → still None
        fake_entities = [
            {"text": "France", "label": "GPE"},
            {"text": "Germany", "label": "GPE"},
        ]
        with patch.object(entity_recognizer, "extract_entities",
                          return_value=fake_entities):
            art = _article(source_id="weird", beats=[],
                           title="War in somewhere", summary="...")
            primary, scores = classifier.classify(art, BEATS_CONFIG)
            assert primary is None  # 0 + 0.15 + 0.10 = 0.25 < 0.45

    def test_entity_boosts_correct_beat_in_multi_candidate(self, _mock_ner):
        """source=[INTL, ECON] 都得 0.6，INTL entity 命中但 ECON 沒有 → INTL 勝出。"""
        fake_entities = [
            {"text": "NATO", "label": "ORG"},
            {"text": "France", "label": "GPE"},
        ]
        with patch.object(entity_recognizer, "extract_entities",
                          return_value=fake_entities):
            art = _article(beats=["INTL", "ECON"],
                           title="Random headline", summary="...")
            primary, scores = classifier.classify(art, BEATS_CONFIG)
            assert primary == "INTL"
            assert scores["INTL"] > scores["ECON"]

    def test_econ_entity_money_and_percent(self, _mock_ner):
        """MONEY + PERCENT → entity_score=1.0 → 加 0.1。"""
        fake_entities = [
            {"text": "$5 billion", "label": "MONEY"},
            {"text": "3.5%", "label": "PERCENT"},
        ]
        with patch.object(entity_recognizer, "extract_entities",
                          return_value=fake_entities):
            art = _article(beats=["ECON"], title="Random", summary="...")
            _, scores = classifier.classify(art, BEATS_CONFIG)
            assert scores["ECON"] == pytest.approx(0.7)

    def test_arts_work_of_art_entity(self, _mock_ner):
        """WORK_OF_ART entity 命中 ARTS beat。"""
        fake_entities = [
            {"text": "Hamlet", "label": "WORK_OF_ART"},
            {"text": "MoMA", "label": "ORG"},
        ]
        with patch.object(entity_recognizer, "extract_entities",
                          return_value=fake_entities):
            art = _article(beats=["ARTS"], title="Random", summary="...")
            _, scores = classifier.classify(art, BEATS_CONFIG)
            # WORK_OF_ART type hit + MoMA name hit = 2 → entity 1.0 → 0.6+0.1=0.7
            assert scores["ARTS"] == pytest.approx(0.7)

    def test_ai_entity_names_openai(self, _mock_ner):
        """OpenAI entity name 命中 AI beat。"""
        fake_entities = [
            {"text": "OpenAI", "label": "ORG"},
            {"text": "Anthropic", "label": "ORG"},
        ]
        with patch.object(entity_recognizer, "extract_entities",
                          return_value=fake_entities):
            art = _article(beats=["AI"], title="Random", summary="...")
            _, scores = classifier.classify(art, BEATS_CONFIG)
            assert scores["AI"] == pytest.approx(0.7)

    def test_keyword_plus_entity_stacks(self, _mock_ner):
        """source(0.6) + keyword ≥2(0.3) + entity ≥2(0.1) = 1.0 滿分。"""
        fake_entities = [
            {"text": "France", "label": "GPE"},
            {"text": "NATO", "label": "ORG"},
        ]
        with patch.object(entity_recognizer, "extract_entities",
                          return_value=fake_entities):
            art = _article(beats=["INTL"],
                           title="Major summit on war and sanctions",
                           summary="Treaty signed")
            _, scores = classifier.classify(art, BEATS_CONFIG)
            assert scores["INTL"] == pytest.approx(1.0)
