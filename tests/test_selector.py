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
