"""Tests for src/claude_rewrite.py — Claude rewrite with mocked SDK."""
import json
from unittest.mock import MagicMock, patch

import pytest

from src.claude_rewrite import (
    prepare_event_payload,
    parse_claude_response,
    call_claude,
    merge_rewrite_into_event,
    rewrite_event,
    rewrite_selected_events,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_event():
    return {
        "event_id": "daily_20260519_evt_001",
        "beat": "INTL",
        "headline": "Russia-Ukraine Geneva talks collapse",
        "context": "The third round of ceasefire negotiations broke down.",
        "article_ids": ["abc123"],
        "sources": [
            {
                "source_id": "bbc_world",
                "name": "BBC News",
                "publisher": "BBC News",
                "summary": "Third round of ceasefire negotiations broke down.",
                "title": "Russia-Ukraine Geneva talks collapse",
                "url": "https://bbc.com/news/123?utm_source=rss",
                "published_at": "2026-05-18T22:30:00Z",
            },
            {
                "source_id": "reuters_world",
                "name": "Reuters",
                "publisher": "Reuters",
                "summary": "Geneva peace talks break down amid territorial disputes.",
                "title": "Geneva peace talks break down",
                "url": "https://reuters.com/456",
                "published_at": "2026-05-18T23:00:00Z",
            },
        ],
        "source_count": 2,
        "source_tiers": [1, 2],
        "tw_highlight": False,
        "selection_score": 45,
        "confidence": "high",
        "claim_trace": [
            {
                "claim": "placeholder",
                "source_id": "bbc_world",
                "source_url": "https://bbc.com/news/123",
                "support_type": "direct",
            }
        ],
    }


@pytest.fixture
def sample_rewrite():
    return {
        "event_id": "daily_20260519_evt_001",
        "headline": "俄烏停火談判第三輪破裂",
        "context": "俄羅斯與烏克蘭在日內瓦的第三輪停火談判宣告破裂，雙方在領土讓步問題上分歧擴大。",
        "thread_text": "🧵 1/2\n📌 國際脈動\n\n俄烏停火談判第三輪破裂\n\n俄羅斯與烏克蘭在日內瓦的第三輪停火談判宣告破裂。",
        "threads_text": "俄烏停火協議第三輪談判在日內瓦破裂，雙方在領土讓步問題上分歧持續擴大。",
        "voice_text": "俄烏第三輪停火談判在日內瓦宣告破裂，雙方在領土讓步問題上分歧持續擴大。",
        "confidence": "high",
        "opinion_level": "none",
        "claim_trace": [
            {
                "claim": "停火談判在日內瓦破裂",
                "source_id": "bbc_world",
                "source_title": "Russia-Ukraine Geneva talks collapse",
                "source_url": "https://bbc.com/news/123",
                "support_type": "direct",
            },
            {
                "claim": "雙方在領土讓步問題上分歧擴大",
                "source_id": "reuters_world",
                "source_title": "Geneva peace talks break down",
                "source_url": "https://reuters.com/456",
                "support_type": "indirect",
            },
        ],
    }


def _make_mock_response(rewrite_dict):
    """建立 mock Anthropic response。"""
    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.text = json.dumps(rewrite_dict, ensure_ascii=False)
    mock_response.content = [mock_block]
    return mock_response


# ---------------------------------------------------------------------------
# prepare_event_payload
# ---------------------------------------------------------------------------

class TestPrepareEventPayload:
    def test_basic_structure(self, sample_event):
        payload = prepare_event_payload(sample_event)
        assert payload["event_id"] == "daily_20260519_evt_001"
        assert payload["beat"] == "INTL"
        assert payload["tw_highlight"] is False
        assert payload["constraints"]["x_max_chars"] == 280
        assert payload["constraints"]["threads_max_chars"] == 500

    def test_cleans_tracking_params(self, sample_event):
        payload = prepare_event_payload(sample_event)
        bbc_url = payload["sources"][0]["url"]
        assert "utm_source" not in bbc_url

    def test_html_cleaning(self, sample_event):
        sample_event["sources"][0]["title"] = "<b>Bold</b> Title"
        payload = prepare_event_payload(sample_event)
        assert "<b>" not in payload["sources"][0]["title"]
        assert "Bold Title" == payload["sources"][0]["title"]

    def test_summary_uses_article_summary_not_name(self, sample_event):
        """HIGH #3: summary 必須來自文章摘要，而非 source name。"""
        payload = prepare_event_payload(sample_event)
        bbc = payload["sources"][0]
        assert bbc["summary"] == "Third round of ceasefire negotiations broke down."
        assert bbc["summary"] != bbc.get("name", "")


# ---------------------------------------------------------------------------
# parse_claude_response
# ---------------------------------------------------------------------------

class TestParseClaudeResponse:
    def test_pure_json(self):
        data = {"headline": "test", "confidence": "high"}
        result = parse_claude_response(json.dumps(data))
        assert result == data

    def test_json_in_code_block(self):
        text = '```json\n{"headline": "test"}\n```'
        result = parse_claude_response(text)
        assert result == {"headline": "test"}

    def test_json_in_code_block_no_lang(self):
        text = '```\n{"headline": "test"}\n```'
        result = parse_claude_response(text)
        assert result == {"headline": "test"}

    def test_invalid_json(self):
        result = parse_claude_response("This is not JSON at all")
        assert result is None

    def test_whitespace_around_json(self):
        result = parse_claude_response('  \n{"a": 1}\n  ')
        assert result == {"a": 1}


# ---------------------------------------------------------------------------
# call_claude
# ---------------------------------------------------------------------------

class TestCallClaude:
    def test_successful_call(self, sample_rewrite):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_response(sample_rewrite)

        result = call_claude(mock_client, "system prompt", {"event_id": "test"})
        assert result is not None
        assert result["headline"] == "俄烏停火談判第三輪破裂"
        mock_client.messages.create.assert_called_once()

    def test_retries_on_failure(self, sample_rewrite):
        mock_client = MagicMock()
        # 第一次失敗，第二次成功
        mock_client.messages.create.side_effect = [
            Exception("API error"),
            _make_mock_response(sample_rewrite),
        ]

        with patch("src.claude_rewrite.RETRY_DELAY", 0):
            result = call_claude(mock_client, "system", {"event_id": "test"})

        assert result is not None
        assert mock_client.messages.create.call_count == 2

    def test_all_retries_fail(self):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Always fails")

        with patch("src.claude_rewrite.RETRY_DELAY", 0):
            result = call_claude(mock_client, "system", {"event_id": "test"})

        assert result is None
        assert mock_client.messages.create.call_count == 3  # 1 + 2 retries


# ---------------------------------------------------------------------------
# merge_rewrite_into_event
# ---------------------------------------------------------------------------

class TestMergeRewriteIntoEvent:
    def test_overwrites_rewrite_fields(self, sample_event, sample_rewrite):
        merged = merge_rewrite_into_event(sample_event, sample_rewrite)
        assert merged["headline"] == "俄烏停火談判第三輪破裂"
        assert merged["confidence"] == "high"
        assert merged["opinion_level"] == "none"

    def test_preserves_structural_fields(self, sample_event, sample_rewrite):
        merged = merge_rewrite_into_event(sample_event, sample_rewrite)
        assert merged["article_ids"] == ["abc123"]
        assert merged["source_count"] == 2
        assert merged["selection_score"] == 45
        assert merged["beat"] == "INTL"

    def test_fixes_claim_trace(self, sample_event, sample_rewrite):
        merged = merge_rewrite_into_event(sample_event, sample_rewrite)
        # claim_trace 應保留有效的 claims
        assert len(merged["claim_trace"]) >= 1
        # source_url 應被修正為 sources 中的值
        for ct in merged["claim_trace"]:
            assert ct["source_id"] in ("bbc_world", "reuters_world")

    def test_single_source_warning(self, sample_event, sample_rewrite):
        sample_event["source_count"] = 1
        merged = merge_rewrite_into_event(sample_event, sample_rewrite)
        assert merged["single_source_warning"] is True

    def test_does_not_mutate_original(self, sample_event, sample_rewrite):
        original_headline = sample_event["headline"]
        merge_rewrite_into_event(sample_event, sample_rewrite)
        assert sample_event["headline"] == original_headline


# ---------------------------------------------------------------------------
# rewrite_event
# ---------------------------------------------------------------------------

class TestRewriteEvent:
    def test_dry_run(self, sample_event):
        result, warnings = rewrite_event(sample_event, None, "", dry_run=True)
        assert result == sample_event
        assert warnings == []

    def test_successful_rewrite(self, sample_event, sample_rewrite):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_response(sample_rewrite)

        result, warnings = rewrite_event(
            sample_event, mock_client, "system prompt",
        )
        assert result["headline"] == "俄烏停火談判第三輪破裂"
        assert result["voice_text"] == "俄烏第三輪停火談判在日內瓦宣告破裂，雙方在領土讓步問題上分歧持續擴大。"

    def test_api_failure_preserves_original(self, sample_event):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("fail")

        with patch("src.claude_rewrite.RETRY_DELAY", 0):
            result, warnings = rewrite_event(
                sample_event, mock_client, "system",
            )
        assert result["headline"] == sample_event["headline"]  # 保留原始
        assert any(w["type"] == "rewrite_failed" for w in warnings)


# ---------------------------------------------------------------------------
# rewrite_selected_events
# ---------------------------------------------------------------------------

class TestRewriteSelectedEvents:
    def test_dry_run_batch(self, sample_event):
        events = [sample_event, {**sample_event, "event_id": "daily_20260519_evt_002"}]
        results, warnings = rewrite_selected_events(
            events, dry_run=True, system_prompt="test",
        )
        assert len(results) == 2
        assert warnings == []

    def test_batch_with_mock_client(self, sample_event, sample_rewrite):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_response(sample_rewrite)

        events = [sample_event]
        results, warnings = rewrite_selected_events(
            events, client=mock_client, system_prompt="test",
        )
        assert len(results) == 1
        assert results[0]["headline"] == "俄烏停火談判第三輪破裂"

    def test_lint_warnings_collected(self, sample_event):
        """rewrite with banned phrase → lint warning collected."""
        bad_rewrite = {
            "headline": "測試",
            "context": "此事據悉已確認",  # 禁用詞
            "voice_text": "測試語音",
            "confidence": "high",
            "opinion_level": "none",
            "claim_trace": [{
                "claim": "test",
                "source_id": "bbc_world",
                "source_url": "https://bbc.com/news/123",
                "support_type": "direct",
            }],
        }
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_response(bad_rewrite)

        results, warnings = rewrite_selected_events(
            [sample_event], client=mock_client, system_prompt="test",
        )
        assert any(w["type"] == "banned_phrase" for w in warnings)
