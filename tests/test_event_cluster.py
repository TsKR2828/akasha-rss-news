"""Phase 2 — event_cluster 單元測試。

對應規格 §7 與 §17（events 必須通過 event.schema.json）。
"""
from __future__ import annotations

import json

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

    def test_source_name_uses_publisher_not_synthetic(self):
        """MEDIUM #5: name 必須用 publisher，不得用 sid.replace().title() 合成。"""
        cluster = [_article("a" * 64, source_id="bbc_world")]
        evt = event_cluster.build_event(cluster, "daily_20260518_evt_001")
        src = evt["sources"][0]
        assert src["name"] == "Pub"  # _article fixture publisher
        assert src["name"] != "Bbc World"  # 不是合成值

    def test_source_carries_article_summary(self):
        """HIGH #3 support: source 必須攜帶文章 summary 以供 rewrite 使用。"""
        cluster = [_article("a" * 64, summary="Ceasefire talks collapsed.")]
        evt = event_cluster.build_event(cluster, "daily_20260518_evt_001")
        src = evt["sources"][0]
        assert src["summary"] == "Ceasefire talks collapsed."


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


# ---------------------------------------------------------------------------
# main() 清理舊事件檔
# ---------------------------------------------------------------------------

class TestMainCleansStaleEvents:
    """CARD-03：main() 重跑前刪除 events 目錄中的舊事件檔，保留 _ 前綴檔。"""

    def test_stale_events_removed_underscore_kept_new_events_written(self, tmp_path):
        """events 目錄預放 1 個過期事件 json + 1 個 _selection_manifest.json；
        跑 main() 後：
        - 過期事件檔消失
        - _selection_manifest.json 仍在
        - 本次新事件檔已寫入
        """
        date_str = "2026-06-01"

        # 建立 articles 目錄並放入 1 篇已分類文章
        articles_dir = tmp_path / "articles" / date_str
        articles_dir.mkdir(parents=True)
        art = _article("a" * 64, source_id="bbc_world", tier=1,
                       title="Ukraine summit held in Brussels",
                       summary="ceasefire talks ongoing")
        (articles_dir / ("a" * 64 + ".json")).write_text(
            json.dumps(art), encoding="utf-8"
        )

        # 建立 events 目錄並預置舊事件檔 + _ 前綴檔
        # 使用不會與本次輸出衝突的檔名（evt_099），確保刪除驗證準確
        events_dir = tmp_path / "events" / date_str
        events_dir.mkdir(parents=True)
        stale_file = events_dir / "daily_20260601_evt_099.json"
        stale_file.write_text(json.dumps({"event_id": "stale_old"}), encoding="utf-8")
        manifest_file = events_dir / "_selection_manifest.json"
        manifest_file.write_text(json.dumps({"selected": []}), encoding="utf-8")

        # 執行 main()
        rc = event_cluster.main([
            "--articles-base", str(tmp_path / "articles"),
            "--events-base", str(tmp_path / "events"),
            "--date", date_str,
        ])
        assert rc == 0

        # 過期事件檔必須消失
        assert not stale_file.exists(), "舊事件檔應已被刪除"

        # _ 前綴檔必須保留
        assert manifest_file.exists(), "_selection_manifest.json 不應被刪除"

        # 本次新事件檔必須寫入
        new_events = [
            f for f in events_dir.iterdir()
            if f.suffix == ".json" and not f.name.startswith("_")
        ]
        assert len(new_events) >= 1, "本次執行應寫入至少 1 個新事件檔"
