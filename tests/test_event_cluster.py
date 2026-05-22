"""Phase 2 — event_cluster 單元測試。

對應規格 §7 與 §17（events 必須通過 event.schema.json）。
"""
from __future__ import annotations

import pytest
from jsonschema import Draft7Validator

from src import event_cluster


def _article(
    aid: str,
    source_id: str = "bbc_world",
    title: str = "Lorem ipsum article",
    summary: str = "Sample summary.",
    canonical: str = "",
    published_at: str = "2026-05-18T01:20:00+08:00",
    beat: str = "INTL",
    tier: int = 1,
    tw_highlight: bool = False,
) -> dict:
    return {
        "article_id": aid,
        "source_id": source_id,
        "publisher": "Pub",
        "tier": tier,
        "beat_candidates": [beat],
        "beat": beat,
        "sub_beat": None,
        "title": title,
        "summary": summary,
        "url": canonical or "https://x.com/" + aid[:6],
        "canonical_url": canonical or "https://x.com/" + aid[:6],
        "published_at": published_at,
        "fetched_at": "2026-05-18T05:00:00+08:00",
        "lang": "en",
        "raw_hash": "z" * 64,
        "tw_highlight": tw_highlight,
        "tw_highlight_reason": "TSMC chip" if tw_highlight else None,
        "tw_highlight_keywords": ["TSMC", "chip"] if tw_highlight else [],
    }


# ---------------------------------------------------------------------------
# matches_cluster
# ---------------------------------------------------------------------------

class TestMatchesCluster:
    def test_same_canonical_url_matches(self):
        a = _article("a" * 64, canonical="https://x.com/1")
        b = _article("b" * 64, canonical="https://x.com/1")
        assert event_cluster.matches_cluster(b, [a])

    def test_similar_title_matches(self):
        a = _article("a" * 64, source_id="bbc_world",
                     title="Major summit on Ukraine war held in Brussels")
        b = _article("b" * 64, source_id="reuters_world",
                     title="Brussels hosts major summit on Ukraine war",
                     canonical="https://reuters.com/2")
        assert event_cluster.matches_cluster(b, [a])

    def test_shared_keywords_matches(self):
        """同 beat + 標題中度相似(≥50%) + 5 個以上共同關鍵詞 → 合併。"""
        a = _article("a" * 64, source_id="bbc_world",
                     title="Ukraine ceasefire talks in Brussels",
                     summary="Ukraine ceasefire negotiation military humanitarian aid package")
        b = _article("b" * 64, source_id="reuters_world",
                     title="Brussels ceasefire conference on Ukraine",
                     summary="Ukraine ceasefire negotiation military humanitarian aid package",
                     canonical="https://reuters.com/2")
        assert event_cluster.matches_cluster(b, [a])

    def test_outside_time_window_does_not_match(self):
        a = _article("a" * 64, title="Major summit on Ukraine war",
                     published_at="2026-05-15T00:00:00+08:00")
        b = _article("b" * 64, title="Major summit on Ukraine war",
                     published_at="2026-05-18T23:00:00+08:00",
                     canonical="https://other.com/2")
        # 兩篇 published_at 差 ~96 小時 > 24h
        assert not event_cluster.matches_cluster(b, [a])

    def test_unrelated_articles_do_not_match(self):
        a = _article("a" * 64, title="Apple releases new iPhone",
                     summary="Tech product launch")
        b = _article("b" * 64, title="Brazil wins football match",
                     summary="Sports result")
        assert not event_cluster.matches_cluster(b, [a])

    def test_cross_beat_keyword_does_not_match(self):
        """不同 beat 的文章不能僅靠共同關鍵詞合併（防止 transitive chain 造成事件爆炸）。"""
        a = _article("a" * 64, source_id="bbc_biz", beat="ECON",
                     title="China trade analysis",
                     summary="Global economy china trade summit agreement")
        b = _article("b" * 64, source_id="reuters_world", beat="INTL",
                     title="Political summit overview",
                     summary="Global economy china trade summit agreement",
                     canonical="https://reuters.com/2")
        # 兩篇共享 >3 個關鍵詞但 beat 不同，不得合併
        assert not event_cluster.matches_cluster(b, [a])

    def test_cross_beat_title_sim_still_matches(self):
        """不同 beat 仍可透過高標題相似度合併（同一事件跨 beat 報導的正常情況）。"""
        a = _article("a" * 64, source_id="bbc_biz", beat="ECON",
                     title="China buys 200 Boeing jets after summit")
        b = _article("b" * 64, source_id="reuters_world", beat="INTL",
                     title="China buys 200 Boeing jets after summit",
                     canonical="https://reuters.com/2")
        assert event_cluster.matches_cluster(b, [a])

    def test_same_beat_low_title_sim_keywords_only_no_match(self):
        """同 beat + 共同關鍵詞夠多，但標題相似度 < 50% → 不合併。
        防止同領域不相關文章黏在一起（如 ARTS 兩篇不同建築報導）。"""
        a = _article("a" * 64, source_id="archdaily", beat="ARTS",
                     title="Concrete walls frame inward-gazing residence in Brazil",
                     summary="architecture residential concrete walls courtyard design")
        b = _article("b" * 64, source_id="dezeen", beat="ARTS",
                     title="Wooden doors and timber screens define Japanese tea house",
                     summary="architecture residential wooden doors courtyard design",
                     canonical="https://dezeen.com/2")
        # 共享 architecture, residential, courtyard, design 等關鍵詞，
        # 但標題完全不同 → 不該合併
        assert not event_cluster.matches_cluster(b, [a])

    def test_same_beat_moderate_title_sim_plus_keywords_matches(self):
        """同 beat + 標題 ≥ 50% 相似 + 共同關鍵詞 ≥ 5 → 合併。"""
        a = _article("a" * 64, source_id="archdaily", beat="ARTS",
                     title="Concrete residence with courtyard in Sao Paulo Brazil",
                     summary="architecture residential concrete walls courtyard inward design")
        b = _article("b" * 64, source_id="dezeen", beat="ARTS",
                     title="Courtyard residence of concrete in Sao Paulo",
                     summary="architecture residential concrete walls courtyard inward design",
                     canonical="https://dezeen.com/2")
        assert event_cluster.matches_cluster(b, [a])


# ---------------------------------------------------------------------------
# cluster_articles
# ---------------------------------------------------------------------------

class TestClusterArticles:
    def test_unrelated_articles_separate_clusters(self):
        articles = [
            _article("a" * 64, title="Apple new iPhone", summary="tech"),
            _article("b" * 64, title="Football match result", summary="sports",
                     canonical="https://x.com/b"),
        ]
        clusters = event_cluster.cluster_articles(articles)
        assert len(clusters) == 2

    def test_related_articles_merged(self):
        articles = [
            _article("a" * 64, source_id="bbc_world",
                     title="Major Ukraine summit in Brussels",
                     summary="Ceasefire negotiation"),
            _article("b" * 64, source_id="reuters_world",
                     title="Brussels hosts Ukraine summit",
                     summary="Ceasefire deal discussed",
                     canonical="https://reuters.com/b"),
        ]
        clusters = event_cluster.cluster_articles(articles)
        assert len(clusters) == 1
        assert len(clusters[0]) == 2

    def test_pts_local_does_not_merge_with_intl(self):
        articles = [
            _article("a" * 64, source_id="pts_news", beat="PTS_LOCAL",
                     title="Taiwan summit on Ukraine",
                     summary="Ceasefire negotiation"),
            _article("b" * 64, source_id="bbc_world", beat="INTL",
                     title="Taiwan summit on Ukraine",
                     summary="Ceasefire negotiation",
                     canonical="https://bbc.com/b"),
        ]
        clusters = event_cluster.cluster_articles(articles)
        assert len(clusters) == 2

    def test_cross_beat_keyword_only_separate_clusters(self):
        """不同 beat + 僅共同關鍵詞 → 分開成不同 cluster。"""
        articles = [
            _article("a" * 64, source_id="bbc_biz", beat="ECON",
                     title="China trade policy update",
                     summary="Beijing economy summit global trade"),
            _article("b" * 64, source_id="dezeen", beat="ARTS",
                     title="Architecture design review",
                     summary="Beijing economy summit global trade",
                     canonical="https://dezeen.com/b"),
        ]
        clusters = event_cluster.cluster_articles(articles)
        assert len(clusters) == 2

    def test_same_beat_unrelated_articles_separate_clusters(self):
        """同 beat 但標題不相似的文章，即使共享領域關鍵詞也不合併。"""
        articles = [
            _article("a" * 64, source_id="archdaily", beat="ARTS",
                     title="Concrete walls frame inward-gazing residence in Brazil",
                     summary="architecture residential concrete walls courtyard design"),
            _article("b" * 64, source_id="dezeen", beat="ARTS",
                     title="Wooden doors and timber screens define Japanese tea house",
                     summary="architecture residential wooden doors courtyard design",
                     canonical="https://dezeen.com/b"),
        ]
        clusters = event_cluster.cluster_articles(articles)
        assert len(clusters) == 2


# ---------------------------------------------------------------------------
# build_event / cluster_to_events
# ---------------------------------------------------------------------------

class TestBuildEvent:
    def test_event_has_required_fields(self):
        cluster = [_article("a" * 64)]
        evt = event_cluster.build_event(cluster, "daily_20260518_evt_001")
        assert evt["event_id"] == "daily_20260518_evt_001"
        assert evt["beat"] == "INTL"
        assert evt["source_count"] == 1
        assert evt["single_source_warning"] is True
        assert len(evt["claim_trace"]) >= 1

    def test_unique_sources_when_same_source_appears_twice(self):
        """同 source 多篇 → sources 只列一次。"""
        cluster = [
            _article("a" * 64, source_id="bbc_world", canonical="https://x/1"),
            _article("b" * 64, source_id="bbc_world", canonical="https://x/2"),
        ]
        evt = event_cluster.build_event(cluster, "daily_20260518_evt_001")
        assert evt["source_count"] == 1  # 同源算一個 source
        assert len(evt["sources"]) == 1
        # 但 article_ids 仍有兩篇
        assert len(evt["article_ids"]) == 2

    def test_multiple_sources(self):
        cluster = [
            _article("a" * 64, source_id="bbc_world", tier=1),
            _article("b" * 64, source_id="reuters_world", tier=1,
                     canonical="https://reuters.com/b"),
        ]
        evt = event_cluster.build_event(cluster, "daily_20260518_evt_001")
        assert evt["source_count"] == 2
        assert evt["single_source_warning"] is False


class TestConfidence:
    def test_two_tier1_sources_high(self):
        cluster = [
            _article("a" * 64, source_id="bbc_world", tier=1),
            _article("b" * 64, source_id="reuters_world", tier=1,
                     canonical="https://r.com/b"),
        ]
        evt = event_cluster.build_event(cluster, "daily_20260518_evt_001")
        assert evt["confidence"] == "high"

    def test_single_tier3_medium(self):
        """單一 Tier 3 來源 → medium（領域權威不該標低）。"""
        cluster = [_article("a" * 64, source_id="marktechpost", tier=3)]
        evt = event_cluster.build_event(cluster, "daily_20260518_evt_001")
        assert evt["confidence"] == "medium"

    def test_single_tier1_medium(self):
        cluster = [_article("a" * 64, source_id="bbc_world", tier=1)]
        evt = event_cluster.build_event(cluster, "daily_20260518_evt_001")
        assert evt["confidence"] == "medium"


class TestTWHighlightPropagation:
    def test_highlight_propagated_to_event(self):
        cluster = [
            _article("a" * 64, source_id="bbc_world", tw_highlight=True),
            _article("b" * 64, source_id="reuters_world", tw_highlight=False,
                     canonical="https://r.com/b"),
        ]
        evt = event_cluster.build_event(cluster, "daily_20260518_evt_001")
        assert evt["tw_highlight"] is True
        assert evt["tw_highlight_reason"] is not None
        assert "TSMC" in evt["tw_highlight_keywords"]


# ---------------------------------------------------------------------------
# Schema conformance
# ---------------------------------------------------------------------------

class TestEventSchemaConformance:
    def test_clustered_event_passes_event_schema(self, event_schema):
        articles = [
            _article("a" * 64, source_id="bbc_world", tier=1,
                     title="Ukraine summit", summary="ceasefire negotiation"),
            _article("b" * 64, source_id="reuters_world", tier=1,
                     title="Ukraine summit", summary="ceasefire negotiation",
                     canonical="https://r.com/b"),
        ]
        events = event_cluster.cluster_to_events(articles, "2026-05-18")
        assert len(events) == 1
        validator = Draft7Validator(event_schema)
        for evt in events:
            validator.validate(evt)
