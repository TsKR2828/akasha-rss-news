"""Phase 2 — classifier 單元測試。

對應規格 §6.1 / §6.2 與 §20.1 P0 / P1。
"""
from __future__ import annotations

import pytest

from src import classifier


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
        },
        "ARTS": {
            "keywords_en": ["pulitzer", "cannes", "exhibition"],
            "keywords_zh": ["影展", "展覽"],
        },
        "AI": {
            "keywords_en": ["ai", "gpt", "llm", "claude", "neural"],
            "keywords_zh": ["大模型"],
        },
        "ECON": {
            "keywords_en": ["fed", "inflation", "tariff"],
            "keywords_zh": ["通膨"],
        },
    },
}


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
