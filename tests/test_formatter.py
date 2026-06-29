"""Phase 4 — Tests for src/formatter.py.

涵蓋：
- split_posts（X 280 字切分 / Threads 500 字切分）
- build_platform_output_item
- build_report（report.schema.json 格式）
- format_markdown
- format_voice_script
- format_x_draft / format_threads_draft
- build_run_log
- validate_report_output
- generate_all_outputs（整合測試）
"""
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.formatter import (
    BEAT_ORDER,
    BEAT_TRANSITION_POOL,
    BEAT_TRANSITIONS,
    THREADS_MAX_CHARS,
    X_MAX_CHARS,
    _build_source_attribution,
    _collect_all_sources,
    _force_split,
    _format_publisher_list,
    _load_fetch_warnings_filtered,
    _split_long_sentence,
    build_platform_output_item,
    build_report,
    build_run_log,
    format_markdown,
    format_threads_draft,
    format_voice_script,
    format_x_draft,
    generate_all_outputs,
    load_beat_meta,
    split_posts,
    validate_report_output,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_event():
    """一個經過 Phase 3 改寫的完整 event。"""
    return {
        "event_id": "daily_20260519_evt_001",
        "beat": "INTL",
        "headline": "測試標題：國際新聞事件",
        "context": "這是一則關於國際情勢的脈絡說明。多個來源確認了這項消息。",
        "thread_text": "🌍 測試標題：國際新聞事件。這是 X 版的內容。",
        "threads_text": "測試標題：國際新聞事件。這是 Threads 版的內容，可以寫比較長。",
        "voice_text": "接下來是一則國際新聞。測試標題，國際新聞事件。多個來源確認了這項消息。",
        "confidence": "high",
        "opinion_level": "none",
        "tw_highlight": False,
        "selection_score": 45,
        "selection_reason": "multi_source_confirmed; source_tier_1",
        "source_count": 2,
        "source_tiers": [1, 1],
        "single_source_warning": False,
        "sources": [
            {
                "source_id": "bbc_world",
                "publisher": "BBC",
                "title": "Test headline from BBC",
                "url": "https://www.bbc.com/news/test",
                "published_at": "2026-05-19T10:00:00+08:00",
            },
            {
                "source_id": "reuters_world",
                "publisher": "Reuters",
                "title": "Test headline from Reuters",
                "url": "https://www.reuters.com/test",
                "published_at": "2026-05-19T11:00:00+08:00",
            },
        ],
        "claim_trace": [
            {
                "claim": "測試事實宣稱",
                "source_id": "bbc_world",
                "source_title": "Test headline from BBC",
                "source_url": "https://www.bbc.com/news/test",
                "support_type": "direct",
            },
        ],
    }


@pytest.fixture
def sample_event_tw():
    """一個台灣相關的 event。"""
    return {
        "event_id": "daily_20260519_evt_002",
        "beat": "INTL",
        "headline": "TSMC 產能擴大計畫",
        "context": "台積電宣布最新產能擴張計畫。",
        "thread_text": "🇹🇼 TSMC 產能擴大計畫。台積電宣布最新產能擴張計畫。",
        "threads_text": "TSMC 產能擴大計畫。台積電宣布最新產能擴張計畫。",
        "voice_text": "接下來是一則與台灣相關的新聞。台積電宣布最新產能擴張計畫。",
        "confidence": "high",
        "opinion_level": "none",
        "tw_highlight": True,
        "tw_highlight_reason": "TSMC in title",
        "tw_highlight_keywords": ["TSMC"],
        "selection_score": 60,
        "source_count": 1,
        "single_source_warning": True,
        "sources": [
            {
                "source_id": "reuters_world",
                "publisher": "Reuters",
                "title": "TSMC expands capacity",
                "url": "https://www.reuters.com/tsmc",
                "published_at": "2026-05-19T09:00:00+08:00",
            },
        ],
        "claim_trace": [
            {
                "claim": "台積電擴產",
                "source_id": "reuters_world",
                "source_title": "TSMC expands capacity",
                "source_url": "https://www.reuters.com/tsmc",
                "support_type": "direct",
            },
        ],
    }


@pytest.fixture
def sample_arts_event():
    """ARTS beat event。"""
    return {
        "event_id": "daily_20260519_evt_003",
        "beat": "ARTS",
        "headline": "坎城影展評審團大獎揭曉",
        "context": "今年坎城影展評審團大獎結果出爐。",
        "thread_text": "🎭 坎城影展評審團大獎揭曉。今年坎城影展評審團大獎結果出爐。",
        "threads_text": "坎城影展評審團大獎揭曉。今年坎城影展評審團大獎結果出爐。",
        "voice_text": "今年坎城影展的評審團大獎結果出爐了。",
        "confidence": "high",
        "opinion_level": "none",
        "tw_highlight": False,
        "selection_score": 30,
        "source_count": 2,
        "sources": [
            {
                "source_id": "guardian_film",
                "publisher": "The Guardian",
                "title": "Cannes Grand Prix announced",
                "url": "https://www.theguardian.com/cannes",
                "published_at": "2026-05-19T08:00:00+08:00",
            },
            {
                "source_id": "nyt_arts",
                "publisher": "NYT",
                "title": "Cannes Film Festival award",
                "url": "https://www.nytimes.com/cannes",
                "published_at": "2026-05-19T08:30:00+08:00",
            },
        ],
        "claim_trace": [
            {
                "claim": "坎城大獎揭曉",
                "source_id": "guardian_film",
                "source_title": "Cannes Grand Prix announced",
                "source_url": "https://www.theguardian.com/cannes",
                "support_type": "direct",
            },
        ],
    }


@pytest.fixture
def sample_stats():
    return {
        "total_feeds_checked": 26,
        "total_feeds_failed": 0,
        "total_feeds_failed_remote_blocked": 0,
        "total_articles_fetched": 461,
        "total_articles_after_filter": 400,
        "total_events_merged": 15,
        "total_events_selected": 10,
        "tw_highlights_count": 1,
    }


@pytest.fixture
def beat_meta():
    return {
        "INTL": {"name": "國際大事", "emoji": "🌍"},
        "ARTS": {"name": "八大藝術", "emoji": "🎭"},
        "AI":   {"name": "AI 新知",  "emoji": "🤖"},
        "ECON": {"name": "全球經濟趨勢", "emoji": "📊"},
        "PTS_LOCAL": {"name": "公視在地新聞", "emoji": "🇹🇼"},
        "TW_STORY":  {"name": "台灣故事", "emoji": "📜"},
    }


# ---------------------------------------------------------------------------
# TestSplitPosts
# ---------------------------------------------------------------------------

class TestSplitPosts:
    """split_posts：把長文切成 ≤ max_chars 的 posts。"""

    def test_short_text_single_post(self):
        result = split_posts("短文字。", 280)
        assert result == ["短文字。"]

    def test_empty_text(self):
        assert split_posts("", 280) == []
        assert split_posts("  ", 280) == []

    def test_exact_limit(self):
        text = "A" * 280
        result = split_posts(text, 280)
        assert len(result) == 1
        assert result[0] == text

    def test_split_at_sentence_boundary(self):
        text = "第一句。第二句。第三句。"
        result = split_posts(text, 10)
        # Each sentence is 3 chars + 。 = 4 chars, two fit in 10
        assert all(len(p) <= 10 for p in result)
        assert len(result) >= 1

    def test_split_long_sentence_at_comma(self):
        text = "這是一段很長的句子，但是可以在逗號切開，因為逗號是合理的切點。"
        result = split_posts(text, 15)
        assert all(len(p) <= 15 for p in result)

    def test_force_split_when_no_punctuation(self):
        text = "A" * 600
        result = split_posts(text, 280)
        assert all(len(p) <= 280 for p in result)
        assert "".join(result) == text

    def test_chinese_text_split(self):
        text = "今天國際上有幾件大事。第一件是關於歐洲的外交峰會。第二件是關於亞洲的貿易協定。第三件是中東的和平談判。"
        result = split_posts(text, 30)
        assert all(len(p) <= 30 for p in result)
        # Should have multiple posts
        assert len(result) >= 2


class TestForceSplit:
    """_force_split：強制按字數截斷。"""

    def test_basic(self):
        result = _force_split("ABCDEF", 3)
        assert result == ["ABC", "DEF"]

    def test_uneven(self):
        result = _force_split("ABCDEFG", 3)
        assert result == ["ABC", "DEF", "G"]

    def test_within_limit(self):
        result = _force_split("AB", 3)
        assert result == ["AB"]


class TestSplitLongSentence:
    """_split_long_sentence：先試逗號，再強制截斷。"""

    def test_comma_split(self):
        text = "一二三四，五六七八，九十"
        result = _split_long_sentence(text, 8)
        assert all(len(p) <= 8 for p in result)

    def test_within_limit(self):
        result = _split_long_sentence("短句", 280)
        assert result == ["短句"]


# ---------------------------------------------------------------------------
# TestBuildPlatformOutputItem
# ---------------------------------------------------------------------------

class TestBuildPlatformOutputItem:
    """build_platform_output_item：把 event 轉成 schema 格式。"""

    def test_basic_structure(self, sample_event):
        item = build_platform_output_item(sample_event)
        assert item["event_id"] == "daily_20260519_evt_001"
        assert item["headline"] == "測試標題：國際新聞事件"
        assert item["beat"] == "INTL"
        assert item["confidence"] == "high"
        assert item["tw_highlight"] is False
        assert item["selection_score"] == 45

    def test_platform_outputs_structure(self, sample_event):
        item = build_platform_output_item(sample_event)
        po = item["platform_outputs"]
        assert po["x"]["max_chars"] == 280
        assert isinstance(po["x"]["posts"], list)
        assert po["threads"]["max_chars"] == 500
        assert isinstance(po["threads"]["posts"], list)
        assert "text" in po["voice"]

    def test_sources_preserved(self, sample_event):
        item = build_platform_output_item(sample_event)
        assert len(item["sources"]) == 2
        assert item["source_count"] == 2

    def test_tw_highlight_reason_added(self, sample_event_tw):
        item = build_platform_output_item(sample_event_tw)
        assert item["tw_highlight"] is True
        assert "tw_highlight_reason" in item

    def test_single_source_warning_auto(self):
        event = {
            "event_id": "evt_test",
            "beat": "INTL",
            "headline": "test",
            "context": "",
            "thread_text": "test",
            "threads_text": "test",
            "voice_text": "test",
            "confidence": "low",
            "sources": [{"source_id": "a", "publisher": "A", "title": "t",
                         "url": "https://a.com", "published_at": "2026-01-01T00:00:00Z"}],
            "source_count": 1,
            "claim_trace": [{"claim": "c", "source_id": "a",
                             "source_url": "https://a.com", "support_type": "direct"}],
            "tw_highlight": False,
            "selection_score": 10,
        }
        item = build_platform_output_item(event)
        assert item["single_source_warning"] is True

    def test_x_posts_split(self):
        long_text = "這是一段很長的文字。" * 40  # ~200 chars
        event = {
            "event_id": "evt_long",
            "beat": "AI",
            "headline": "test",
            "context": "",
            "thread_text": long_text,
            "threads_text": "短",
            "voice_text": "短",
            "confidence": "medium",
            "sources": [{"source_id": "a", "publisher": "A", "title": "t",
                         "url": "https://a.com", "published_at": "2026-01-01T00:00:00Z"}],
            "source_count": 1,
            "claim_trace": [],
            "tw_highlight": False,
            "selection_score": 10,
        }
        item = build_platform_output_item(event)
        x_posts = item["platform_outputs"]["x"]["posts"]
        assert all(len(p) <= X_MAX_CHARS for p in x_posts)


# ---------------------------------------------------------------------------
# TestBuildReport
# ---------------------------------------------------------------------------

class TestBuildReport:
    """build_report：組裝 report.schema.json 格式。"""

    def test_report_structure(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)

        assert report["reportId"] == "daily_20260519"
        assert report["date"] == "2026-05-19"
        assert report["timezone"] == "Asia/Taipei"
        assert report["status"] == "ok"
        assert "generated_at" in report
        assert isinstance(report["warnings"], list)
        assert isinstance(report["sections"], list)
        assert isinstance(report["stats"], dict)

    def test_sections_ordered_by_beat(self, sample_event, sample_arts_event, sample_stats, beat_meta):
        items = [
            build_platform_output_item(sample_arts_event),
            build_platform_output_item(sample_event),
        ]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        beats = [s["beat"] for s in report["sections"]]
        # INTL comes before ARTS in BEAT_ORDER
        assert beats.index("INTL") < beats.index("ARTS")

    def test_sections_have_title_emoji(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        section = report["sections"][0]
        assert section["title"] == "國際大事"
        assert section["emoji"] == "🌍"

    def test_status_partial_on_warnings(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        warnings = [{"type": "lint_warning", "message": "test warning"}]
        report = build_report("2026-05-19", items, [], warnings, sample_stats, beat_meta)
        assert report["status"] == "partial"

    def test_status_failed_no_sections(self, sample_stats, beat_meta):
        report = build_report("2026-05-19", [], [], [], sample_stats, beat_meta)
        assert report["status"] == "failed"

    def test_dropped_events_included(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        dropped = [{"event_id": "evt_drop", "headline": "被丟棄",
                     "selection_score": 5, "drop_reason": "beat_limit_reached"}]
        report = build_report("2026-05-19", items, dropped, [], sample_stats, beat_meta)
        assert "dropped_events" in report
        assert len(report["dropped_events"]) == 1
        assert report["dropped_events"][0]["drop_reason"] == "beat_limit_reached"

    def test_stats_normalized(self, sample_event, beat_meta):
        items = [build_platform_output_item(sample_event)]
        partial_stats = {"total_feeds_checked": 26}
        report = build_report("2026-05-19", items, [], [], partial_stats, beat_meta)
        stats = report["stats"]
        assert stats["total_feeds_checked"] == 26
        assert stats["total_feeds_failed"] == 0  # default
        assert stats["total_events_selected"] == 0  # default

    def test_empty_beats_not_in_sections(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]  # only INTL
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        beats = [s["beat"] for s in report["sections"]]
        assert "ARTS" not in beats
        assert "INTL" in beats

    def test_items_sorted_by_selection_score(self, sample_event, sample_event_tw, sample_stats, beat_meta):
        """同 beat 內的事件按 selection_score 降序排列。"""
        # sample_event score=45, sample_event_tw score=60, both INTL beat
        items = [
            build_platform_output_item(sample_event),      # score 45
            build_platform_output_item(sample_event_tw),    # score 60
        ]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        intl_section = [s for s in report["sections"] if s["beat"] == "INTL"][0]
        scores = [it.get("selection_score", 0) for it in intl_section["items"]]
        assert scores == sorted(scores, reverse=True)  # 高分在前


# ---------------------------------------------------------------------------
# TestFormatMarkdown
# ---------------------------------------------------------------------------

class TestFormatMarkdown:
    """format_markdown：Markdown 可讀版。"""

    def test_has_header(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        md = format_markdown(report, beat_meta)
        assert "阿卡夏圖書館" in md
        assert "2026-05-19" in md

    def test_has_beat_headings(self, sample_event, sample_arts_event, sample_stats, beat_meta):
        items = [
            build_platform_output_item(sample_event),
            build_platform_output_item(sample_arts_event),
        ]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        md = format_markdown(report, beat_meta)
        assert "🌍 國際大事" in md
        assert "🎭 八大藝術" in md

    def test_has_headlines(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        md = format_markdown(report, beat_meta)
        assert "測試標題：國際新聞事件" in md

    def test_has_stats_table(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        md = format_markdown(report, beat_meta)
        assert "統計" in md
        assert "461" in md  # total_articles_fetched

    def test_tw_highlight_mark(self, sample_event_tw, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event_tw)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        md = format_markdown(report, beat_meta)
        assert "🇹🇼" in md

    def test_has_reference_links_section(self, sample_event, sample_stats, beat_meta):
        """Markdown 底部有「📎 參考來源」區塊。"""
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        md = format_markdown(report, beat_meta)
        assert "📎 參考來源" in md
        assert "bbc.com" in md


# ---------------------------------------------------------------------------
# TestFormatVoiceScript
# ---------------------------------------------------------------------------

class TestFormatVoiceScript:
    """format_voice_script：朗讀稿。"""

    def test_has_opening(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        voice = format_voice_script(report, "2026-05-19", beat_meta)
        assert "早安，這裡是阿卡夏圖書館。" in voice
        assert "2026 年 5 月 19 日" in voice
        assert "星期二" in voice  # 2026-05-19 is Tuesday
        # 「讓圖書館員翻譯給你聽」只在開場出現一次
        assert "讓圖書館員翻譯給你聽" in voice
        assert voice.count("讓圖書館員翻譯給你聽") == 1

    def test_has_beat_transition(self, sample_event, sample_stats, beat_meta):
        """voice 裡應包含 INTL beat 的某個過場句（從 pool 隨機選取）。"""
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        voice = format_voice_script(report, "2026-05-19", beat_meta)
        # 隨機選取 pool 中的任一句，至少命中一句
        assert any(t in voice for t in BEAT_TRANSITION_POOL["INTL"])

    def test_has_voice_text(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        voice = format_voice_script(report, "2026-05-19", beat_meta)
        assert sample_event["voice_text"] in voice

    def test_no_per_event_attribution(self, sample_event, sample_stats, beat_meta):
        """Formatter 不在每則後面加來源宣告（開場白除外）。"""
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        voice = format_voice_script(report, "2026-05-19", beat_meta)
        # 「讓圖書館員翻譯給你聽」只出現在開場白，不在每則後面重複
        assert voice.count("讓圖書館員翻譯給你聽") == 1
        # 不應有 formatter 生成的 per-event 來源行
        assert "本則整理自" not in voice
        assert "本館報來自" not in voice

    def test_has_closing(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        voice = format_voice_script(report, "2026-05-19", beat_meta)
        assert "以上是今天的館報。" in voice
        assert "我們明天見。" in voice

    def test_not_thread_text_stripped(self, sample_event, sample_stats, beat_meta):
        """朗讀版獨立生成，不是拿 thread_text 刪 emoji。"""
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        voice = format_voice_script(report, "2026-05-19", beat_meta)
        # voice_text 和 thread_text 內容不同
        assert sample_event["voice_text"] in voice
        # thread_text 有 emoji，voice script 不應該有
        assert "🌍" not in voice

    def test_no_urls_in_voice(self, sample_event, sample_stats, beat_meta):
        """Voice 版不含 URL（TTS 不該唸連結，連結只在 markdown 版）。"""
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        voice = format_voice_script(report, "2026-05-19", beat_meta)
        assert "https://" not in voice
        assert "http://" not in voice

    def test_consolidated_source_line(self, sample_event, sample_stats, beat_meta):
        """結尾有統一來源宣告：「以上新聞來自 BBC 與 Reuters 的報導。」"""
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        voice = format_voice_script(report, "2026-05-19", beat_meta)
        assert "以上新聞來自" in voice
        assert "BBC" in voice
        assert "Reuters" in voice
        # 確認在「我們明天見」之前
        source_idx = voice.index("以上新聞來自")
        closing_idx = voice.index("我們明天見")
        assert source_idx < closing_idx

    def test_same_date_str_produces_identical_output(self, sample_event, sample_stats, beat_meta):
        """同 date_str 呼叫 format_voice_script 兩次，輸出字串完全相等（確定性）。"""
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        voice_first = format_voice_script(report, "2026-05-19", beat_meta)
        voice_second = format_voice_script(report, "2026-05-19", beat_meta)
        assert voice_first == voice_second

    def test_voice_reads_all_events_fully(self, sample_event, sample_stats, beat_meta):
        """voice 版完整朗讀每一則，不設展開上限，不用「另外還有」頓號串列帶過。"""
        # 建 10 個 INTL 事件，score 100~10
        events = []
        for i in range(10):
            evt = {
                **sample_event,
                "event_id": f"daily_20260519_evt_{i+1:03d}",
                "headline": f"測試標題{i+1}",
                "voice_text": f"這是第 {i+1} 則完整語音內容。",
                "selection_score": 100 - i * 10,
            }
            events.append(evt)

        items = [build_platform_output_item(e) for e in events]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        voice = format_voice_script(report, "2026-05-19", beat_meta)

        # 10 則全部完整展開
        for i in range(1, 11):
            assert f"這是第 {i} 則完整語音內容。" in voice
        # 不再有「另外還有」頓號串列（rewrite_prompt 明令禁止之格式錯誤）
        assert "另外還有" not in voice

    def test_no_banned_template_transitions(self):
        """換場語 pool 不得含 rewrite_prompt 明令禁止的模板標籤。"""
        banned = {
            "換個節奏，看建築。",
            "然後是 AI 的部分。",
            "財經面。",
            "科技那邊。",
            "換到經濟。",
        }
        all_transitions = {
            t for pool in BEAT_TRANSITION_POOL.values() for t in pool
        }
        assert not (banned & all_transitions)


class TestFormatPublisherList:
    """_format_publisher_list：結尾統一來源宣告。"""

    def test_single(self):
        assert _format_publisher_list(["BBC"]) == "以上新聞來自BBC的報導。"

    def test_two(self):
        result = _format_publisher_list(["BBC", "Reuters"])
        assert result == "以上新聞來自BBC與Reuters的報導。"

    def test_three(self):
        result = _format_publisher_list(["BBC", "NPR", "ArchDaily"])
        assert result == "以上新聞來自BBC、NPR與ArchDaily的報導。"

    def test_empty(self):
        assert _format_publisher_list([]) == ""


class TestBuildSourceAttribution:
    """_build_source_attribution：來源宣告。"""

    def test_single_source(self):
        sources = [{"publisher": "BBC"}]
        result = _build_source_attribution(sources, "2026-05-19")
        assert "BBC" in result
        assert "2026 年 5 月 19 日" in result
        assert "讓圖書館員翻譯給你聽" in result

    def test_multi_source(self):
        sources = [{"publisher": "BBC"}, {"publisher": "Reuters"}, {"publisher": "AP"}]
        result = _build_source_attribution(sources, "2026-05-19")
        assert "BBC" in result
        assert "Reuters" in result
        assert "AP" in result
        assert "整理自" in result

    def test_empty_sources(self):
        result = _build_source_attribution([], "2026-05-19")
        assert result == ""


# ---------------------------------------------------------------------------
# TestPlatformDrafts
# ---------------------------------------------------------------------------

class TestFormatXDraft:
    def test_structure(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        draft = format_x_draft(report)
        assert draft["platform"] == "x"
        assert draft["max_chars_per_post"] == 280
        assert len(draft["events"]) == 1
        assert "posts" in draft["events"][0]

    def test_event_data(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        draft = format_x_draft(report)
        evt = draft["events"][0]
        assert evt["event_id"] == "daily_20260519_evt_001"
        assert evt["beat"] == "INTL"
        assert evt["headline"] == "測試標題：國際新聞事件"


class TestFormatThreadsDraft:
    def test_structure(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        draft = format_threads_draft(report)
        assert draft["platform"] == "threads"
        assert draft["max_chars_per_post"] == 500
        assert len(draft["events"]) == 1


# ---------------------------------------------------------------------------
# TestBuildRunLog
# ---------------------------------------------------------------------------

class TestBuildRunLog:
    def test_structure(self, sample_stats):
        start = time.time() - 10
        log = build_run_log("2026-05-19", [], [], sample_stats, start)
        assert log["reportId"] == "daily_20260519"
        assert log["date"] == "2026-05-19"
        assert log["timezone"] == "Asia/Taipei"
        assert log["status"] == "ok"
        assert log["duration_seconds"] >= 10
        assert log["warnings_count"] == 0

    def test_includes_steps(self, sample_stats):
        steps = [{"name": "fetch_rss", "status": "ok", "duration": 5.2}]
        log = build_run_log("2026-05-19", steps, [], sample_stats, time.time())
        assert len(log["steps"]) == 1
        assert log["steps"][0]["name"] == "fetch_rss"


# ---------------------------------------------------------------------------
# TestValidateReportOutput
# ---------------------------------------------------------------------------

class TestValidateReportOutput:
    def test_clean_report_no_issues(self, sample_event, sample_stats, beat_meta):
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        issues = validate_report_output(report)
        assert issues == []

    def test_voice_text_url_flagged(self, sample_event, sample_stats, beat_meta):
        sample_event["voice_text"] = "查看 https://example.com 了解更多"
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        issues = validate_report_output(report)
        assert any("URL" in i.get("message", "") or "url" in i.get("message", "").lower()
                    for i in issues)

    def test_x_post_oversize_flagged(self, sample_event, sample_stats, beat_meta):
        sample_event["thread_text"] = "A" * 300  # single post over 280
        items = [build_platform_output_item(sample_event)]
        # Manually override the split to test validation
        items[0]["platform_outputs"]["x"]["posts"] = ["A" * 300]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        issues = validate_report_output(report)
        assert any("X post" in i.get("message", "") for i in issues)

    def test_missing_claim_trace_flagged(self, sample_event, sample_stats, beat_meta):
        sample_event["claim_trace"] = []
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        issues = validate_report_output(report)
        assert any("claim_trace" in i.get("message", "") for i in issues)


# ---------------------------------------------------------------------------
# TestLoadBeatMeta
# ---------------------------------------------------------------------------

class TestLoadBeatMeta:
    def test_loads_from_file(self):
        meta = load_beat_meta()
        assert "INTL" in meta
        assert meta["INTL"]["name"] == "國際大事"
        assert meta["INTL"]["emoji"] == "🌍"

    def test_fallback_on_missing_file(self, tmp_path):
        meta = load_beat_meta(tmp_path / "nonexistent.yaml")
        assert "INTL" in meta  # fallback kicks in


# ---------------------------------------------------------------------------
# TestGenerateAllOutputs (integration)
# ---------------------------------------------------------------------------

class TestGenerateAllOutputs:
    def test_dry_run(self, sample_event, sample_stats):
        report, issues = generate_all_outputs(
            date_str="2026-05-19",
            rewritten_events=[sample_event],
            dropped_events=[],
            pipeline_warnings=[],
            pipeline_stats=sample_stats,
            dry_run=True,
        )
        assert report["reportId"] == "daily_20260519"
        assert len(report["sections"]) >= 1

    def test_writes_all_files(self, sample_event, sample_arts_event, sample_stats, tmp_path):
        report, issues = generate_all_outputs(
            date_str="2026-05-19",
            rewritten_events=[sample_event, sample_arts_event],
            dropped_events=[],
            pipeline_warnings=[],
            pipeline_stats=sample_stats,
            output_base=tmp_path,
        )

        assert (tmp_path / "daily_20260519.json").exists()
        assert (tmp_path / "daily_20260519.md").exists()
        assert (tmp_path / "voice_20260519.txt").exists()
        assert (tmp_path / "platforms" / "x_20260519.json").exists()
        assert (tmp_path / "platforms" / "threads_20260519.json").exists()
        assert (tmp_path / "logs" / "run_20260519.json").exists()

    def test_json_output_valid(self, sample_event, sample_stats, tmp_path):
        generate_all_outputs(
            date_str="2026-05-19",
            rewritten_events=[sample_event],
            dropped_events=[],
            pipeline_warnings=[],
            pipeline_stats=sample_stats,
            output_base=tmp_path,
        )

        # Verify JSON is parseable
        report = json.loads((tmp_path / "daily_20260519.json").read_text(encoding="utf-8"))
        assert report["reportId"] == "daily_20260519"
        assert report["timezone"] == "Asia/Taipei"

    def test_multiple_beats_in_report(self, sample_event, sample_arts_event, sample_stats, tmp_path):
        report, _ = generate_all_outputs(
            date_str="2026-05-19",
            rewritten_events=[sample_event, sample_arts_event],
            dropped_events=[],
            pipeline_warnings=[],
            pipeline_stats=sample_stats,
            output_base=tmp_path,
        )
        beats = [s["beat"] for s in report["sections"]]
        assert "INTL" in beats
        assert "ARTS" in beats

    def test_validation_issues_in_warnings(self, sample_event, sample_stats, tmp_path):
        sample_event["voice_text"] = "有 URL https://bad.com 在朗讀稿"
        report, issues = generate_all_outputs(
            date_str="2026-05-19",
            rewritten_events=[sample_event],
            dropped_events=[],
            pipeline_warnings=[],
            pipeline_stats=sample_stats,
            output_base=tmp_path,
        )
        assert len(issues) > 0
        assert report["status"] == "partial"


# ---------------------------------------------------------------------------
# CLI stats reading
# ---------------------------------------------------------------------------

class TestCLIStatsReading:
    """formatter CLI 的 main() 應從 feed_health.json 和 articles 目錄讀取實際統計，
    不再硬編碼為 0。"""

    def test_stats_from_feed_health(self, sample_event, tmp_path):
        """CLI 能從 feed_health.json 讀到實際 article 數量。"""
        date = "2026-05-19"

        # 建立 data/raw/date/feed_health.json
        raw_dir = tmp_path / "data" / "raw" / date
        raw_dir.mkdir(parents=True)
        health = [
            {"source_id": "bbc_world", "status": "ok", "items_valid": 30},
            {"source_id": "reuters_world", "status": "ok", "items_valid": 25},
            {"source_id": "bad_feed", "status": "error", "items_valid": 0},
        ]
        (raw_dir / "feed_health.json").write_text(
            json.dumps(health), encoding="utf-8"
        )

        # 建立 data/articles/date/ 下的文章檔案
        articles_dir = tmp_path / "data" / "articles" / date
        articles_dir.mkdir(parents=True)
        for i in range(40):
            (articles_dir / f"art_{i:03d}.json").write_text("{}", encoding="utf-8")
        # _metadata 檔不應計入
        (articles_dir / "_metadata.json").write_text("{}", encoding="utf-8")

        # 建立 events/date/ 目錄 + manifest + event 檔
        events_dir = tmp_path / "data" / "events" / date
        events_dir.mkdir(parents=True)
        eid = sample_event["event_id"]
        (events_dir / f"{eid}.json").write_text(
            json.dumps(sample_event, ensure_ascii=False), encoding="utf-8"
        )
        manifest = {"selected_event_ids": [eid], "dropped": []}
        (events_dir / "_selection_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

        # Patch PROJECT_ROOT so formatter CLI looks in tmp_path
        from src import formatter
        original_root = formatter.PROJECT_ROOT
        formatter.PROJECT_ROOT = tmp_path

        try:
            output_dir = tmp_path / "output"
            rc = formatter.main([
                "--date", date,
                "--events-base", str(events_dir.parent),
                "--output-base", str(output_dir),
            ])
            assert rc == 0

            # 從 run log 讀回 stats
            dc = date.replace("-", "")
            log_path = output_dir / "logs" / f"run_{dc}.json"
            assert log_path.exists()
            run_log = json.loads(log_path.read_text(encoding="utf-8"))
            stats = run_log["stats"]

            assert stats["total_feeds_checked"] == 3
            assert stats["total_feeds_failed"] == 1
            assert stats["total_articles_fetched"] == 55  # 30 + 25
            assert stats["total_articles_after_filter"] == 40  # 不含 _metadata
        finally:
            formatter.PROJECT_ROOT = original_root


# ---------------------------------------------------------------------------
# TestLoadFetchWarningsFiltered — CARD-06
# ---------------------------------------------------------------------------

class TestLoadFetchWarningsFiltered:
    """_load_fetch_warnings_filtered：讀取 fetch_warnings.json 並過濾 remote_blocked 來源。"""

    def test_no_file_returns_empty(self, tmp_path):
        from src import formatter
        original_root = formatter.PROJECT_ROOT
        formatter.PROJECT_ROOT = tmp_path
        try:
            result = _load_fetch_warnings_filtered("2026-05-20")
            assert result == []
        finally:
            formatter.PROJECT_ROOT = original_root

    def test_filters_remote_blocked_keeps_real_fail(self, tmp_path):
        """remote_blocked 來源的 warning 應被過濾；真失敗來源應保留。"""
        from src import formatter
        original_root = formatter.PROJECT_ROOT
        formatter.PROJECT_ROOT = tmp_path

        # 建立 feeds.yaml
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True)
        feeds_yaml = (
            "sources:\n"
            "  - source_id: rb_src\n"
            "    remote_blocked: true\n"
            "  - source_id: real_fail_src\n"
            "    remote_blocked: false\n"
        )
        (config_dir / "feeds.yaml").write_text(feeds_yaml, encoding="utf-8")

        # 建立 fetch_warnings.json
        raw_dir = tmp_path / "data" / "raw" / "2026-05-20"
        raw_dir.mkdir(parents=True)
        warnings = [
            {"source_id": "rb_src", "type": "source_failed", "message": "remote blocked"},
            {"source_id": "real_fail_src", "type": "source_failed", "message": "真失敗"},
        ]
        (raw_dir / "fetch_warnings.json").write_text(
            json.dumps(warnings), encoding="utf-8"
        )

        try:
            result = _load_fetch_warnings_filtered("2026-05-20")
        finally:
            formatter.PROJECT_ROOT = original_root

        assert len(result) == 1
        assert result[0]["source_id"] == "real_fail_src"
        assert result[0]["type"] == "source_failed"


class TestFormatterMainFetchWarnings:
    """CARD-06：formatter.main 的 CLI 單跑路徑也讀取並過濾 fetch warnings。"""

    def test_fetch_warning_real_fail_causes_partial(self, sample_event, tmp_path):
        """fetch_warnings.json 含 1 個 remote_blocked 源 + 1 個真失敗源 →
        formatter.main 報告 warnings 只含真失敗、status partial、return 1。"""
        from src import formatter

        date = "2026-05-20"

        # 建立 events
        events_dir = tmp_path / "events" / date
        events_dir.mkdir(parents=True)
        eid = "daily_20260520_evt_001"
        evt = dict(sample_event)
        evt["event_id"] = eid
        (events_dir / f"{eid}.json").write_text(
            json.dumps(evt, ensure_ascii=False), encoding="utf-8"
        )
        manifest = {"selected_event_ids": [eid], "dropped": []}
        (events_dir / "_selection_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

        # 建立 feeds.yaml：rb_src 是 remote_blocked
        original_root = formatter.PROJECT_ROOT
        formatter.PROJECT_ROOT = tmp_path
        try:
            config_dir = tmp_path / "config"
            config_dir.mkdir(parents=True)
            feeds_yaml = (
                "sources:\n"
                "  - source_id: rb_src\n"
                "    remote_blocked: true\n"
                "  - source_id: real_fail_src\n"
                "    remote_blocked: false\n"
            )
            (config_dir / "feeds.yaml").write_text(feeds_yaml, encoding="utf-8")

            # 建立 fetch_warnings.json
            raw_dir = tmp_path / "data" / "raw" / date
            raw_dir.mkdir(parents=True)
            fetch_warnings_data = [
                {"source_id": "rb_src", "type": "source_failed", "message": "remote blocked"},
                {"source_id": "real_fail_src", "type": "source_failed", "message": "真失敗"},
            ]
            (raw_dir / "fetch_warnings.json").write_text(
                json.dumps(fetch_warnings_data), encoding="utf-8"
            )

            output_dir = tmp_path / "output"
            rc = formatter.main([
                "--date", date,
                "--events-base", str(tmp_path / "events"),
                "--output-base", str(output_dir),
            ])
        finally:
            formatter.PROJECT_ROOT = original_root

        # status partial → exit 1
        assert rc == 1

        # 驗證報告中 warnings 只含真失敗
        dc = date.replace("-", "")
        report_path = output_dir / f"daily_{dc}.json"
        assert report_path.exists()
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["status"] == "partial"
        source_failed_warnings = [
            w for w in report["warnings"]
            if w.get("type") == "source_failed"
        ]
        assert len(source_failed_warnings) == 1
        assert source_failed_warnings[0].get("source_id") == "real_fail_src"


# ---------------------------------------------------------------------------
# TestMainExitCodes — CARD-09
# ---------------------------------------------------------------------------

def _make_events_dir(tmp_path: Path, date: str, events: list, manifest_extra: dict | None = None) -> Path:
    """輔助：在 tmp_path 下建立符合 CLI 要求的 events 目錄結構。"""
    events_dir = tmp_path / date
    events_dir.mkdir(parents=True, exist_ok=True)
    selected_ids = []
    for evt in events:
        eid = evt["event_id"]
        selected_ids.append(eid)
        (events_dir / f"{eid}.json").write_text(
            json.dumps(evt, ensure_ascii=False), encoding="utf-8"
        )
    manifest: dict = {"selected_event_ids": selected_ids, "dropped": []}
    if manifest_extra:
        manifest.update(manifest_extra)
    (events_dir / "_selection_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )
    return events_dir.parent  # events_base


class TestMainExitCodes:
    """main() 依 report status 回傳正確 exit code。"""

    def test_exit_0_clean_report(self, sample_event, tmp_path):
        """正常 event、無違規 → report.status='ok' → return 0。"""
        date = "2026-05-20"
        events_base = _make_events_dir(tmp_path / "events", date, [sample_event])
        output_dir = tmp_path / "output"

        from src import formatter
        rc = formatter.main([
            "--date", date,
            "--events-base", str(events_base),
            "--output-base", str(output_dir),
        ])
        assert rc == 0

    def test_exit_1_lint_violation(self, sample_event, tmp_path):
        """voice_text 含 URL → validate_report_output 產生 issue
        → report.status='partial' → return 1。"""
        date = "2026-05-21"
        evt = dict(sample_event)
        evt["event_id"] = "daily_20260521_evt_001"
        evt["voice_text"] = "詳見 https://bad.example.com 的完整報導。"

        events_base = _make_events_dir(tmp_path / "events", date, [evt])
        output_dir = tmp_path / "output"

        from src import formatter
        rc = formatter.main([
            "--date", date,
            "--events-base", str(events_base),
            "--output-base", str(output_dir),
        ])
        assert rc == 1

    def test_exit_2_no_sections(self, tmp_path):
        """空 selected_event_ids → 無 sections → report.status='failed' → return 2。"""
        date = "2026-05-22"
        # 建立空 manifest，無任何 event 檔
        events_dir = tmp_path / "events" / date
        events_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": [], "dropped": []}
        (events_dir / "_selection_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )
        output_dir = tmp_path / "output"

        from src import formatter
        rc = formatter.main([
            "--date", date,
            "--events-base", str(tmp_path / "events"),
            "--output-base", str(output_dir),
        ])
        assert rc == 2
