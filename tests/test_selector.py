"""Phase 2 — selector 單元測試。

對應規格 §8.1 / §8.2 / §8.3。
"""
from __future__ import annotations

import pytest

from src import selector


SCORE_CONFIG = {
    "daily_limits": {
        "INTL": {"min": 2, "max": 3},
        "ARTS": {"min": 1, "max": 2},
        "AI": {"min": 1, "max": 2},
        "ECON": {"min": 1, "max": 2},
        "PTS_LOCAL": {"min": 1, "max": 2},
    },
    "selection_score": {
        "multi_source_confirmed": 30,
        "taiwan_related_foreign_report": 30,
        "major_geopolitical_event": 25,
        "direct_public_impact": 20,
        "source_tier_1": 15,
        "source_tier_2": 8,
        "source_tier_3": 3,
        "arts_major_award_or_institution": 15,
        "ai_major_model_or_policy": 20,
        "economy_macro_policy": 20,
        "same_topic_already_selected": -20,
        "single_low_tier_source": -15,
    },
}


def _event(
    event_id: str = "daily_20260518_evt_001",
    beat: str = "INTL",
    source_count: int = 1,
    source_tiers: list = None,
    tw_highlight: bool = False,
    headline: str = "Lorem ipsum",
    context: str = "",
    sources: list = None,
) -> dict:
    if sources is None and source_count >= 2:
        # 多來源預設用不同媒體（2026-09-26 起多來源加分看媒體數）
        outlets = ["bbc_world", "npr_world", "aljazeera_all", "guardian_culture"]
        sources = [
            {"source_id": outlets[i % len(outlets)], "publisher": "P",
             "title": "x", "url": f"https://x.com/{i + 1}",
             "published_at": "2026-05-18T01:20:00+08:00"}
            for i in range(source_count)
        ]
    return {
        "event_id": event_id,
        "beat": beat,
        "headline": headline,
        "context": context,
        "source_count": source_count,
        "source_tiers": source_tiers if source_tiers is not None else [1],
        "tw_highlight": tw_highlight,
        "sources": sources or [{"source_id": "bbc_world", "publisher": "BBC",
                                 "title": "x", "url": "https://x.com/1",
                                 "published_at": "2026-05-18T01:20:00+08:00"}],
        "selection_score": 0,
    }


# ---------------------------------------------------------------------------
# score_event
# ---------------------------------------------------------------------------

class TestSourceBonuses:
    def test_single_tier1_source(self):
        e = _event(source_tiers=[1])
        score, rules = selector.score_event(e, SCORE_CONFIG)
        # tier 1 = +15
        assert score == 15
        assert "source_tier_1" in rules

    def test_multi_source_confirmed_bonus(self):
        e = _event(source_count=2, source_tiers=[1, 2])
        score, rules = selector.score_event(e, SCORE_CONFIG)
        # multi(30) + tier1(15) + tier2(8) = 53
        assert score == 53
        assert "multi_source_confirmed" in rules

    def test_same_outlet_channels_not_multi_source(self):
        """同一家媒體的兩個頻道（路透 world + business）不算多方確認。"""
        e = _event(
            source_count=2, source_tiers=[1],
            sources=[
                {"source_id": "reuters_world_google_news", "title": "a",
                 "url": "https://r.com/a"},
                {"source_id": "reuters_business_google_news", "title": "b",
                 "url": "https://r.com/b"},
            ],
        )
        score, rules = selector.score_event(e, SCORE_CONFIG)
        assert "multi_source_confirmed" not in rules
        assert score == 15

    def test_single_low_tier_source_penalty(self):
        e = _event(source_count=1, source_tiers=[3])
        score, rules = selector.score_event(e, SCORE_CONFIG)
        # tier3(3) + single_low_tier(-15) = -12
        assert score == -12
        assert "single_low_tier_source" in rules


class TestTaiwanBonus:
    def test_foreign_source_with_tw_highlight(self):
        e = _event(
            tw_highlight=True,
            sources=[{"source_id": "bbc_world", "publisher": "BBC",
                      "title": "x", "url": "https://x.com",
                      "published_at": "2026-05-18T01:20:00+08:00"}],
        )
        score, rules = selector.score_event(e, SCORE_CONFIG)
        assert "taiwan_related_foreign_report" in rules

    def test_pts_local_with_tw_highlight_no_bonus(self):
        """公視本身的 highlight 不算 foreign report。"""
        e = _event(
            tw_highlight=True,
            sources=[{"source_id": "pts_news", "publisher": "公視",
                      "title": "x", "url": "https://pts.org.tw",
                      "published_at": "2026-05-18T01:20:00+08:00"}],
        )
        score, rules = selector.score_event(e, SCORE_CONFIG)
        assert "taiwan_related_foreign_report" not in rules


class TestBeatSignalBonus:
    def test_intl_war_keyword_boosts(self):
        e = _event(beat="INTL", headline="Summit on Ukraine war held")
        score, rules = selector.score_event(e, SCORE_CONFIG)
        assert "major_geopolitical_event" in rules

    def test_arts_pulitzer_keyword_boosts(self):
        e = _event(beat="ARTS", headline="Pulitzer Prize for Fiction awarded")
        score, rules = selector.score_event(e, SCORE_CONFIG)
        assert "arts_major_award_or_institution" in rules

    def test_ai_gpt_keyword_boosts(self):
        e = _event(beat="AI", headline="OpenAI releases GPT-5 today")
        score, rules = selector.score_event(e, SCORE_CONFIG)
        assert "ai_major_model_or_policy" in rules

    def test_econ_fed_keyword_boosts(self):
        e = _event(beat="ECON", headline="Fed raises interest rate again")
        score, rules = selector.score_event(e, SCORE_CONFIG)
        assert "economy_macro_policy" in rules

    def test_no_signal_keyword_no_beat_bonus(self):
        e = _event(beat="INTL", headline="Local festival opens this weekend")
        score, rules = selector.score_event(e, SCORE_CONFIG)
        assert "major_geopolitical_event" not in rules


# ---------------------------------------------------------------------------
# select_events
# ---------------------------------------------------------------------------

class TestDailyLimits:
    def test_max_limit_enforced(self):
        events = [
            _event(event_id=f"daily_20260518_evt_{i:03d}", beat="INTL",
                   source_count=2, source_tiers=[1, 1],
                   headline=f"Summit topic {i}")  # 加 summit 確保 selection_score 高
            for i in range(1, 6)  # 5 events
        ]
        selected, dropped = selector.select_events(events, SCORE_CONFIG)
        intl_selected = [e for e in selected if e["beat"] == "INTL"]
        # INTL max=3
        assert len(intl_selected) == 3
        assert len(dropped) == 2
        for d in dropped:
            assert d["drop_reason"] == "beat_limit_reached"

    def test_dropped_events_have_selection_score_too(self):
        events = [
            _event(event_id=f"daily_20260518_evt_{i:03d}", beat="INTL",
                   source_count=1, source_tiers=[1])
            for i in range(1, 6)
        ]
        selected, dropped = selector.select_events(events, SCORE_CONFIG)
        for d in dropped:
            assert "selection_score" in d
            assert d["drop_reason"] is not None


class TestOrdering:
    def test_higher_score_selected_first_within_beat(self):
        e_low = _event(event_id="daily_20260518_evt_001", beat="INTL",
                       source_count=1, source_tiers=[3])  # low
        e_high = _event(event_id="daily_20260518_evt_002", beat="INTL",
                        source_count=2, source_tiers=[1, 1])  # high
        selected, _ = selector.select_events([e_low, e_high], SCORE_CONFIG)
        # both fit (max=3), but high score should sort first
        intl = [e for e in selected if e["beat"] == "INTL"]
        assert intl[0]["event_id"] == e_high["event_id"]

    def test_beat_output_order_intl_arts_ai_econ(self):
        events = [
            _event(event_id="evt_econ", beat="ECON",
                   headline="Fed raises rates", source_tiers=[1]),
            _event(event_id="evt_intl", beat="INTL",
                   headline="Major summit", source_tiers=[1]),
            _event(event_id="evt_arts", beat="ARTS",
                   headline="Pulitzer winner", source_tiers=[1]),
            _event(event_id="evt_ai", beat="AI",
                   headline="GPT-5 released", source_tiers=[1]),
        ]
        # 修正 event_id format - selector 用 event_id 排序作為 tiebreak
        for e in events:
            e["event_id"] = f"daily_20260518_evt_{events.index(e)+1:03d}"
        selected, _ = selector.select_events(events, SCORE_CONFIG)
        beats_in_order = [e["beat"] for e in selected]
        assert beats_in_order == ["INTL", "ARTS", "AI", "ECON"]


class TestTotalEventsMax:
    def test_total_max_enforced(self):
        """#7: total_events.max 超出時，最低分者被 drop（但保護 beat min）。"""
        config = {
            **SCORE_CONFIG,
            "daily_limits": {
                "INTL": {"min": 0, "max": 5},
                "ARTS": {"min": 0, "max": 5},
                "AI": {"min": 0, "max": 5},
                "ECON": {"min": 0, "max": 5},
                "total_events": {"min": 1, "max": 3},
            },
        }
        events = [
            _event(event_id=f"daily_20260518_evt_{i:03d}", beat=beat,
                   source_count=1, source_tiers=[1])
            for i, beat in enumerate(["INTL", "INTL", "ARTS", "AI", "ECON"], 1)
        ]
        selected, dropped = selector.select_events(events, config)
        assert len(selected) == 3
        total_dropped = [d for d in dropped if d.get("drop_reason") == "total_limit_reached"]
        assert len(total_dropped) == 2

    def test_total_max_protects_beat_min(self):
        """total_events.max 裁切不可讓 beat 低於 min。"""
        config = {
            **SCORE_CONFIG,
            "daily_limits": {
                "INTL": {"min": 1, "max": 5},
                "PTS_LOCAL": {"min": 1, "max": 2},
                "total_events": {"min": 1, "max": 2},
            },
        }
        events = [
            _event(event_id="daily_20260518_evt_001", beat="INTL",
                   source_count=2, source_tiers=[1, 2]),
            _event(event_id="daily_20260518_evt_002", beat="INTL",
                   source_count=1, source_tiers=[1]),
            _event(event_id="daily_20260518_evt_003", beat="PTS_LOCAL",
                   source_count=1, source_tiers=["TW"]),
        ]
        selected, dropped = selector.select_events(events, config)
        pts = [e for e in selected if e["beat"] == "PTS_LOCAL"]
        assert len(pts) == 1, "PTS_LOCAL min=1 must be protected"
        assert len(selected) <= 3

    def test_no_total_limit_by_default(self):
        """total_events 未設定時不限制。"""
        no_total = {
            **SCORE_CONFIG,
            "daily_limits": {
                "INTL": {"min": 0, "max": 99},
                "ARTS": {"min": 0, "max": 99},
                "AI": {"min": 0, "max": 99},
                "ECON": {"min": 0, "max": 99},
            },
        }
        events = [
            _event(event_id=f"daily_20260518_evt_{i:03d}",
                   beat=["INTL", "ARTS", "AI", "ECON"][i % 4],
                   source_count=1, source_tiers=[1])
            for i in range(10)
        ]
        selected, _ = selector.select_events(events, no_total)
        assert len(selected) == 10


class TestSameTopicPenalty:
    def test_same_topic_already_selected_penalty_applied(self):
        e1 = _event(event_id="daily_20260518_evt_001", beat="INTL",
                    headline="Brussels summit Ukraine ceasefire",
                    context="negotiation diplomatic peace",
                    source_count=2, source_tiers=[1, 1])
        e2 = _event(event_id="daily_20260518_evt_002", beat="INTL",
                    headline="Ukraine ceasefire negotiation in Brussels",
                    context="summit peace diplomatic",
                    source_count=1, source_tiers=[1])
        selected, dropped = selector.select_events([e1, e2], SCORE_CONFIG)
        # 兩個都進，但 e2 被罰 -20
        intl = [e for e in selected if e["beat"] == "INTL"]
        # 找 e2，確認 selection_reason 含 same_topic_already_selected
        second = next(e for e in intl if e["event_id"] == e2["event_id"])
        assert "same_topic_already_selected" in (second["selection_reason"] or "")


# ---------------------------------------------------------------------------
# reported_recently (cross-day dedup)
# ---------------------------------------------------------------------------

class TestLoadRecentReports:
    def test_loads_urls_and_titles_from_past_days(self, tmp_path):
        import json
        report = {
            "sections": [{
                "beat": "INTL",
                "items": [{
                    "sources": [
                        {"url": "https://example.com/old-story", "title": "Old Story Title"},
                        {"url": "https://example.com/another", "title": "Another Article"},
                    ],
                }],
            }],
        }
        (tmp_path / "daily_20260617.json").write_text(
            json.dumps(report), encoding="utf-8",
        )
        result = selector.load_recent_reports(tmp_path, "2026-06-18", lookback_days=3)
        assert "https://example.com/old-story" in result["urls"]
        assert "https://example.com/another" in result["urls"]
        assert len(result["titles"]) == 2

    def test_ignores_missing_days(self, tmp_path):
        result = selector.load_recent_reports(tmp_path, "2026-06-18", lookback_days=3)
        assert result["urls"] == set()
        assert result["titles"] == []

    def test_skips_corrupt_json(self, tmp_path):
        (tmp_path / "daily_20260617.json").write_text("NOT JSON", encoding="utf-8")
        result = selector.load_recent_reports(tmp_path, "2026-06-18", lookback_days=1)
        assert result["urls"] == set()


class TestMatchesRecentReport:
    def test_url_exact_match(self):
        event = _event(sources=[{
            "source_id": "bbc", "publisher": "BBC",
            "title": "ChatGPT generates bad images",
            "url": "https://bbc.com/article/123",
            "published_at": "2026-06-18T01:00:00+08:00",
        }])
        recent = {
            "urls": {"https://bbc.com/article/123"},
            "titles": [],
        }
        assert selector._matches_recent_report(event, recent) is True

    def test_title_fuzzy_match(self):
        event = _event(sources=[{
            "source_id": "bbc", "publisher": "BBC",
            "title": "ChatGPT generates inappropriate images for users",
            "url": "https://bbc.com/new-url",
            "published_at": "2026-06-18T01:00:00+08:00",
        }])
        recent = {
            "urls": set(),
            "titles": ["chatgpt generates inappropriate images for some users"],
        }
        assert selector._matches_recent_report(event, recent) is True

    def test_no_match_different_topic(self):
        event = _event(sources=[{
            "source_id": "bbc", "publisher": "BBC",
            "title": "Fed raises interest rates sharply",
            "url": "https://bbc.com/fed-rates",
            "published_at": "2026-06-18T01:00:00+08:00",
        }])
        recent = {
            "urls": {"https://other.com/old"},
            "titles": ["chatgpt generates inappropriate images"],
        }
        assert selector._matches_recent_report(event, recent) is False

    def test_empty_recent_returns_false(self):
        event = _event()
        assert selector._matches_recent_report(event, {"urls": set(), "titles": []}) is False


class TestReportedRecentlyPenalty:
    SCORE_CONFIG_WITH_RECENT = {
        **SCORE_CONFIG,
        "selection_score": {
            **SCORE_CONFIG["selection_score"],
            "reported_recently": -40,
        },
    }

    def test_exact_url_match_is_dropped(self):
        """引用前幾天館報的同一篇報導 → 直接不選（2026-09-26 OPS-3）。"""
        e = _event(
            event_id="daily_20260618_evt_001", beat="INTL",
            source_count=2, source_tiers=[1, 2],
            sources=[
                {"source_id": "bbc", "publisher": "BBC",
                 "title": "Story X", "url": "https://bbc.com/story-x",
                 "published_at": "2026-06-18T01:00:00+08:00"},
                {"source_id": "reuters", "publisher": "Reuters",
                 "title": "Story X too", "url": "https://reuters.com/story-x",
                 "published_at": "2026-06-18T02:00:00+08:00"},
            ],
        )
        recent = {
            "urls": {"https://bbc.com/story-x"},
            "titles": [],
        }
        selected, dropped = selector.select_events(
            [e], self.SCORE_CONFIG_WITH_RECENT, recent_reports=recent,
        )
        assert selected == []
        assert dropped[0]["drop_reason"] == "reported_recently"
        assert "reported_recently" in (dropped[0]["selection_reason"] or "")
        assert dropped[0]["selection_score"] < 53

    def test_similar_title_gets_penalty_only(self):
        """只有標題相似（不同網址）→ 扣分但不硬擋。"""
        e = _event(
            event_id="daily_20260618_evt_001", beat="INTL",
            source_count=1, source_tiers=[1],
            sources=[{"source_id": "bbc_world", "title": "Booker prize shortlist announced",
                      "url": "https://bbc.com/new-url"}],
        )
        recent = {"urls": {"https://other.com/old"},
                  "titles": ["booker prize shortlist announced"]}
        selected, dropped = selector.select_events(
            [e], self.SCORE_CONFIG_WITH_RECENT, recent_reports=recent,
        )
        assert len(selected) == 1
        assert "reported_recently" in selected[0]["selection_reason"]
        assert selected[0]["selection_score"] == 15 - 40

    def test_no_penalty_without_recent_reports(self):
        e = _event(
            event_id="daily_20260618_evt_001", beat="INTL",
            source_count=2, source_tiers=[1, 2],
        )
        selected, _ = selector.select_events(
            [e], self.SCORE_CONFIG_WITH_RECENT, recent_reports=None,
        )
        assert "reported_recently" not in (selected[0]["selection_reason"] or "")

    def test_not_a_hard_block(self):
        """網址不同時 reported_recently 不是硬擋——分夠高照樣選入。"""
        e = _event(
            event_id="daily_20260618_evt_001", beat="INTL",
            source_count=2, source_tiers=[1, 1],
            headline="Major summit on Ukraine war ceasefire",
        )
        recent = {"urls": {"https://other.com/9"}, "titles": ["x"]}
        selected, dropped = selector.select_events(
            [e], self.SCORE_CONFIG_WITH_RECENT, recent_reports=recent,
        )
        assert len(selected) == 1
        assert len(dropped) == 0
        assert "reported_recently" in selected[0]["selection_reason"]


class TestLoadRecentReports:
    def test_reads_local_files_and_counts_days(self, tmp_path):
        import json
        report = {"sections": [{"items": [{"sources": [
            {"url": "https://a.com/1", "title": "Story One"}]}]}]}
        (tmp_path / "daily_20260925.json").write_text(json.dumps(report), encoding="utf-8")
        recent = selector.load_recent_reports(tmp_path, "2026-09-26", 3, use_git=False)
        assert recent["loaded_days"] == 1
        assert "https://a.com/1" in recent["urls"]

    def test_falls_back_to_git_when_local_missing(self, tmp_path, monkeypatch):
        """雲端 clone 沒有 output/ 時，從 daily-reports 分支補讀。"""
        import json
        report = {"sections": [{"items": [{"sources": [
            {"url": "https://a.com/git", "title": "From git"}]}]}]}
        calls = []

        def fake_show(filename, repo_root=None):
            calls.append(filename)
            return json.dumps(report) if filename == "daily_20260924.json" else None

        monkeypatch.setattr(selector, "_git_show_report", fake_show)
        monkeypatch.setattr(selector, "_ensure_reports_branch", lambda *a, **k: None)
        recent = selector.load_recent_reports(tmp_path, "2026-09-26", 3, use_git=True)
        assert calls == ["daily_20260925.json", "daily_20260924.json", "daily_20260923.json"]
        assert recent["loaded_days"] == 1
        assert "https://a.com/git" in recent["urls"]

    def test_no_history_writes_manifest_warning(self, tmp_path, monkeypatch):
        import json
        events_dir = tmp_path / "events" / "2026-09-26"
        events_dir.mkdir(parents=True)
        (events_dir / "daily_20260926_evt_001.json").write_text(json.dumps(_event(
            event_id="daily_20260926_evt_001")), encoding="utf-8")
        cfg = tmp_path / "score.yaml"
        import yaml
        cfg.write_text(yaml.safe_dump(SCORE_CONFIG), encoding="utf-8")
        rc = selector.main([
            "--date", "2026-09-26", "--events-base", str(tmp_path / "events"),
            "--output-base", str(tmp_path / "out"), "--score-config", str(cfg),
            "--no-git-history",
        ])
        assert rc == 0
        manifest = json.loads((events_dir / "_selection_manifest.json").read_text(encoding="utf-8"))
        assert manifest["cross_day_history_days"] == 0
        assert "跨日去重無歷史資料" in manifest["warnings"][0]["message"]


class TestWholeWordSignals:
    def test_substring_does_not_trigger_signal(self):
        """Warren 不是 war、senator 不是 NATO（2026-09-26 SEL-7）。"""
        e = _event(beat="INTL", headline="Senator Warren criticises budget")
        assert not selector._signal_keyword_hit(e)

    def test_plural_still_matches(self):
        e = _event(beat="ECON", headline="New tariffs announced on steel")
        assert selector._signal_keyword_hit(e)


class TestSameTopicReplacement:
    def test_second_same_topic_event_is_replaced(self):
        """同主題第二則被扣分後，要讓位給分數較低但不同主題的新聞（2026-09-30）。"""
        cfg = {**SCORE_CONFIG, "daily_limits": {"ECON": {"min": 1, "max": 2}},
               "selection_score": {**SCORE_CONFIG["selection_score"],
                                   "same_topic_already_selected": -45}}
        a = _event(event_id="e1", beat="ECON", source_tiers=[1],
                   headline="US China agree tariff cut worth billions")
        b = _event(event_id="e2", beat="ECON", source_tiers=[1],
                   headline="China US tariff cut agreement reached", sources=[
                       {"source_id": "npr_world", "title": "x", "url": "https://x.com/b"}])
        c = _event(event_id="e3", beat="ECON", source_tiers=[2],
                   headline="Japan service inflation hits two-year high", sources=[
                       {"source_id": "npr_world", "title": "y", "url": "https://x.com/c"}])
        selected, dropped = selector.select_events([a, b, c], cfg)
        assert {e["event_id"] for e in selected} == {"e1", "e3"}
        dup = next(e for e in dropped if e["event_id"] == "e2")
        assert "same_topic_already_selected" in dup["selection_reason"]
        assert dup["drop_reason"] == "beat_limit_reached"


class TestTopicKeywords:
    def test_plural_forms_count_as_same_word(self):
        a = selector._topic_keywords("China and US cut reciprocal tariffs on goods")
        b = selector._topic_keywords("China, US agree to tariff cuts on goods")
        assert len(a & b) >= 3
