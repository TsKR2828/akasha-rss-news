"""Tests for src/validators.py — banned phrases, voice lint, confidence, claim trace."""
import pytest

from src.validators import (
    validate_banned_phrases,
    validate_voice_text,
    validate_confidence,
    validate_claim_trace,
    validate_opinion_level,
    validate_platform_lengths,
    lint_rewrite_output,
)


# ---------------------------------------------------------------------------
# validate_banned_phrases
# ---------------------------------------------------------------------------

class TestBannedPhrases:
    def test_no_banned_words(self):
        assert validate_banned_phrases("這是一則正常的新聞報導") == []

    def test_single_banned_word(self):
        warnings = validate_banned_phrases("根據報導，這件事據悉已經確認")
        assert len(warnings) == 1
        assert warnings[0]["phrase"] == "據悉"

    def test_multiple_banned_words(self):
        text = "有鑑於此，此事備受矚目，值得一提的是相關單位表示"
        warnings = validate_banned_phrases(text)
        phrases = {w["phrase"] for w in warnings}
        assert "有鑑於此" in phrases
        assert "備受矚目" in phrases
        assert "值得一提的是" in phrases
        assert "相關單位表示" in phrases

    def test_all_eight_banned(self):
        all_banned = [
            "據悉", "有鑑於此", "引發關注", "受到矚目",
            "備受矚目", "值得一提的是", "不容忽視", "相關單位表示",
        ]
        for phrase in all_banned:
            warnings = validate_banned_phrases(f"前文{phrase}後文")
            assert len(warnings) >= 1, f"未偵測到禁用詞：{phrase}"

    def test_empty_text(self):
        assert validate_banned_phrases("") == []


# ---------------------------------------------------------------------------
# validate_voice_text
# ---------------------------------------------------------------------------

class TestVoiceText:
    def test_clean_voice_text(self):
        assert validate_voice_text("俄烏第三輪停火談判在日內瓦破裂") == []

    def test_contains_url(self):
        warnings = validate_voice_text("詳見 https://bbc.com/news 報導")
        assert any("URL" in w["pattern"] for w in warnings)

    def test_contains_thread_emoji(self):
        warnings = validate_voice_text("🧵 接下來說說")
        assert any("🧵" in w["pattern"] for w in warnings)

    def test_contains_pin_emoji(self):
        warnings = validate_voice_text("📌 重點新聞")
        assert any("📌" in w["pattern"] for w in warnings)

    def test_contains_clip_emoji(self):
        warnings = validate_voice_text("📎 附件")
        assert any("📎" in w["pattern"] for w in warnings)

    def test_contains_numbering(self):
        warnings = validate_voice_text("1/3 第一則新聞")
        assert any("N/N" in w["pattern"] for w in warnings)

    def test_contains_markdown_link(self):
        warnings = validate_voice_text("來源 [BBC](https://bbc.com)")
        assert any("Markdown" in w["pattern"] for w in warnings)

    def test_empty_voice_text(self):
        warnings = validate_voice_text("")
        assert len(warnings) == 1
        assert warnings[0]["pattern"] == "empty"

    def test_multiple_violations(self):
        text = "🧵 1/3 詳見 https://bbc.com"
        warnings = validate_voice_text(text)
        assert len(warnings) >= 3


# ---------------------------------------------------------------------------
# validate_confidence
# ---------------------------------------------------------------------------

class TestConfidence:
    def test_high_correct(self):
        sources = [
            {"source_id": "a", "publisher": "A"},
            {"source_id": "b", "publisher": "B"},
        ]
        tiers = [1, 2]
        assert validate_confidence("high", sources, tiers) is None

    def test_medium_correct(self):
        sources = [{"source_id": "a"}]
        tiers = [1]
        assert validate_confidence("medium", sources, tiers) is None

    def test_low_correct(self):
        sources = [{"source_id": "a"}]
        tiers = [3]
        assert validate_confidence("low", sources, tiers) is None

    def test_mismatch_warns(self):
        sources = [{"source_id": "a"}]
        tiers = [3]
        warning = validate_confidence("high", sources, tiers)
        assert warning is not None
        assert warning["type"] == "confidence_mismatch"
        assert warning["expected"] == "low"

    def test_invalid_value(self):
        warning = validate_confidence("very_high", [], [])
        assert warning is not None
        assert warning["type"] == "confidence_invalid"


# ---------------------------------------------------------------------------
# validate_claim_trace
# ---------------------------------------------------------------------------

class TestClaimTrace:
    @pytest.fixture
    def sources(self):
        return [
            {"source_id": "bbc_world", "url": "https://bbc.com/1"},
            {"source_id": "reuters_world", "url": "https://reuters.com/1"},
        ]

    def test_valid_claim_trace(self, sources):
        ct = [{
            "claim": "停火談判破裂",
            "source_id": "bbc_world",
            "source_url": "https://bbc.com/1",
            "support_type": "direct",
        }]
        assert validate_claim_trace(ct, sources) == []

    def test_empty_claim_trace(self, sources):
        errors = validate_claim_trace([], sources)
        assert len(errors) == 1
        assert errors[0]["type"] == "claim_trace_empty"

    def test_missing_source_id(self, sources):
        ct = [{"claim": "test", "source_id": "", "support_type": "direct"}]
        errors = validate_claim_trace(ct, sources)
        assert any(e["type"] == "claim_no_source_id" for e in errors)

    def test_unknown_source_id(self, sources):
        ct = [{
            "claim": "test",
            "source_id": "unknown_source",
            "support_type": "direct",
        }]
        errors = validate_claim_trace(ct, sources)
        assert any(e["type"] == "claim_source_not_found" for e in errors)

    def test_empty_claim_text(self, sources):
        ct = [{"claim": "", "source_id": "bbc_world", "support_type": "direct"}]
        errors = validate_claim_trace(ct, sources)
        assert any(e["type"] == "claim_empty" for e in errors)

    def test_invalid_support_type(self, sources):
        ct = [{
            "claim": "test",
            "source_id": "bbc_world",
            "support_type": "maybe",
        }]
        errors = validate_claim_trace(ct, sources)
        assert any(e["type"] == "claim_invalid_support_type" for e in errors)

    def test_multiple_errors(self, sources):
        ct = [
            {"claim": "", "source_id": "", "support_type": "invalid"},
            {"claim": "ok", "source_id": "bbc_world", "support_type": "direct"},
        ]
        errors = validate_claim_trace(ct, sources)
        assert len(errors) >= 3  # empty claim + no source_id + invalid support


# ---------------------------------------------------------------------------
# validate_opinion_level
# ---------------------------------------------------------------------------

class TestOpinionLevel:
    def test_valid_values(self):
        for v in ("none", "light_context", "explicit_commentary"):
            assert validate_opinion_level(v) is None

    def test_invalid_value(self):
        warning = validate_opinion_level("strongly_opinionated")
        assert warning is not None
        assert warning["type"] == "opinion_level_invalid"


# ---------------------------------------------------------------------------
# validate_platform_lengths
# ---------------------------------------------------------------------------

class TestPlatformLengths:
    def test_normal_length(self):
        assert validate_platform_lengths("短文", "中等長度的文字") == []

    def test_thread_text_absurdly_long(self):
        warnings = validate_platform_lengths("x" * 3000, "ok")
        assert any("thread_text" in w["type"] for w in warnings)

    def test_threads_text_absurdly_long(self):
        warnings = validate_platform_lengths("ok", "x" * 3000)
        assert any("threads_text" in w["type"] for w in warnings)


# ---------------------------------------------------------------------------
# lint_rewrite_output (integration)
# ---------------------------------------------------------------------------

class TestLintRewriteOutput:
    def test_clean_output_no_warnings(self):
        rewrite = {
            "headline": "台海局勢升溫",
            "context": "美國總統發表聲明，重申對台灣的支持。",
            "thread_text": "🧵 1/2 台海最新動態",
            "threads_text": "台海局勢最新發展...",
            "voice_text": "美國總統今天發表聲明，重申對台灣的支持。",
            "confidence": "high",
            "opinion_level": "none",
            "claim_trace": [{
                "claim": "美國總統發表聲明",
                "source_id": "bbc_world",
                "source_url": "https://bbc.com/1",
                "support_type": "direct",
            }],
        }
        sources = [
            {"source_id": "bbc_world"},
            {"source_id": "reuters_world"},
        ]
        tiers = [1, 2]
        warnings = lint_rewrite_output(rewrite, sources, tiers)
        assert warnings == []

    def test_banned_word_in_context(self):
        rewrite = {
            "headline": "測試",
            "context": "此事據悉已確認",
            "voice_text": "測試語音",
            "confidence": "medium",
            "opinion_level": "none",
            "claim_trace": [{"claim": "t", "source_id": "a", "support_type": "direct"}],
        }
        sources = [{"source_id": "a"}]
        warnings = lint_rewrite_output(rewrite, sources, [1])
        assert any(w["type"] == "banned_phrase" for w in warnings)

    def test_voice_text_url_lint(self):
        rewrite = {
            "headline": "測試",
            "context": "ok",
            "voice_text": "詳見 https://bbc.com",
            "confidence": "medium",
            "opinion_level": "none",
            "claim_trace": [{"claim": "t", "source_id": "a", "support_type": "direct"}],
        }
        sources = [{"source_id": "a"}]
        warnings = lint_rewrite_output(rewrite, sources, [1])
        assert any(w["type"] == "voice_text_lint" for w in warnings)
