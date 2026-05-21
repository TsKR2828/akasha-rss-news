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
    BEAT_TRANSITIONS,
    THREADS_MAX_CHARS,
    X_MAX_CHARS,
    _build_source_attribution,
    _collect_all_sources,
    _force_split,
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
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        voice = format_voice_script(report, "2026-05-19", beat_meta)
        assert BEAT_TRANSITIONS["INTL"] in voice

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

    def test_has_reference_links(self, sample_event, sample_stats, beat_meta):
        """底部有參考來源連結（方便貼社群留言區）。"""
        items = [build_platform_output_item(sample_event)]
        report = build_report("2026-05-19", items, [], [], sample_stats, beat_meta)
        voice = format_voice_script(report, "2026-05-19", beat_meta)
        assert "參考來源" in voice
        assert "bbc.com" in voice
        assert "reuters.com" in voice


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
