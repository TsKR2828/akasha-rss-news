"""Tests for src/claim_trace.py — claim trace verification and fixing."""
import pytest

from src.claim_trace import (
    verify_claim_trace,
    fix_claim_trace,
    verify_and_fix_claim_trace,
    derive_single_source_warning,
)


@pytest.fixture
def two_sources():
    return [
        {
            "source_id": "bbc_world",
            "publisher": "BBC News",
            "title": "Russia-Ukraine talks collapse",
            "url": "https://bbc.com/news/123",
            "published_at": "2026-05-18T22:00:00Z",
        },
        {
            "source_id": "reuters_world",
            "publisher": "Reuters",
            "title": "Geneva peace talks break down",
            "url": "https://reuters.com/456",
            "published_at": "2026-05-18T23:00:00Z",
        },
    ]


@pytest.fixture
def single_source():
    return [
        {
            "source_id": "bbc_world",
            "publisher": "BBC News",
            "title": "Breaking news",
            "url": "https://bbc.com/news/789",
            "published_at": "2026-05-18T22:00:00Z",
        },
    ]


# ---------------------------------------------------------------------------
# verify_claim_trace
# ---------------------------------------------------------------------------

class TestVerifyClaimTrace:
    def test_valid_claims(self, two_sources):
        ct = [
            {
                "claim": "停火談判破裂",
                "source_id": "bbc_world",
                "source_url": "https://bbc.com/news/123",
                "support_type": "direct",
            },
            {
                "claim": "雙方在領土讓步問題上分歧擴大",
                "source_id": "reuters_world",
                "source_url": "https://reuters.com/456",
                "support_type": "indirect",
            },
        ]
        assert verify_claim_trace(ct, two_sources) == []

    def test_empty_claim_trace(self, two_sources):
        issues = verify_claim_trace([], two_sources)
        assert len(issues) == 1
        assert issues[0]["type"] == "no_claims"

    def test_unknown_source_id(self, two_sources):
        ct = [{
            "claim": "test",
            "source_id": "nyt_world",
            "source_url": "https://nyt.com",
            "support_type": "direct",
        }]
        issues = verify_claim_trace(ct, two_sources)
        assert any(i["type"] == "unknown_source_id" for i in issues)
        assert "nyt_world" in issues[0].get("source_id", "")

    def test_empty_claim_text(self, two_sources):
        ct = [{
            "claim": "",
            "source_id": "bbc_world",
            "support_type": "direct",
        }]
        issues = verify_claim_trace(ct, two_sources)
        assert any(i["type"] == "empty_claim" for i in issues)

    def test_missing_source_id(self, two_sources):
        ct = [{"claim": "test", "support_type": "direct"}]
        issues = verify_claim_trace(ct, two_sources)
        assert any(i["type"] == "missing_source_id" for i in issues)

    def test_invalid_support_type(self, two_sources):
        ct = [{
            "claim": "test",
            "source_id": "bbc_world",
            "support_type": "maybe",
        }]
        issues = verify_claim_trace(ct, two_sources)
        assert any(i["type"] == "invalid_support_type" for i in issues)

    def test_all_three_support_types_valid(self, two_sources):
        for st in ("direct", "indirect", "background"):
            ct = [{"claim": "test", "source_id": "bbc_world", "support_type": st}]
            assert verify_claim_trace(ct, two_sources) == []


# ---------------------------------------------------------------------------
# fix_claim_trace
# ---------------------------------------------------------------------------

class TestFixClaimTrace:
    def test_fixes_source_url(self, two_sources):
        ct = [{
            "claim": "test",
            "source_id": "bbc_world",
            "source_url": "https://wrong.com",
            "support_type": "direct",
        }]
        fixed = fix_claim_trace(ct, two_sources)
        assert fixed[0]["source_url"] == "https://bbc.com/news/123"

    def test_fills_missing_source_title(self, two_sources):
        ct = [{
            "claim": "test",
            "source_id": "bbc_world",
            "source_url": "https://bbc.com/news/123",
            "support_type": "direct",
        }]
        fixed = fix_claim_trace(ct, two_sources)
        assert fixed[0]["source_title"] == "Russia-Ukraine talks collapse"

    def test_removes_invalid_source_id(self, two_sources):
        ct = [
            {"claim": "ok", "source_id": "bbc_world", "support_type": "direct"},
            {"claim": "bad", "source_id": "fake_source", "support_type": "direct"},
        ]
        fixed = fix_claim_trace(ct, two_sources)
        assert len(fixed) == 1
        assert fixed[0]["source_id"] == "bbc_world"

    def test_fixes_invalid_support_type(self, two_sources):
        ct = [{
            "claim": "test",
            "source_id": "bbc_world",
            "support_type": "guessed",
        }]
        fixed = fix_claim_trace(ct, two_sources)
        assert fixed[0]["support_type"] == "direct"

    def test_does_not_mutate_original(self, two_sources):
        ct = [{"claim": "test", "source_id": "bbc_world", "support_type": "direct"}]
        original_url = ct[0].get("source_url")
        fix_claim_trace(ct, two_sources)
        assert ct[0].get("source_url") == original_url


# ---------------------------------------------------------------------------
# verify_and_fix_claim_trace
# ---------------------------------------------------------------------------

class TestVerifyAndFix:
    def test_valid_pass_through(self, two_sources):
        event = {"sources": two_sources, "headline": "Test"}
        ct = [{
            "claim": "停火談判破裂",
            "source_id": "bbc_world",
            "source_url": "https://bbc.com/news/123",
            "support_type": "direct",
        }]
        fixed, issues = verify_and_fix_claim_trace(ct, event)
        assert len(fixed) == 1
        assert issues == []

    def test_fallback_when_all_invalid(self, single_source):
        event = {"sources": single_source, "headline": "Breaking"}
        ct = [{"claim": "x", "source_id": "unknown", "support_type": "direct"}]
        fixed, issues = verify_and_fix_claim_trace(ct, event)
        assert len(fixed) == 1
        assert fixed[0]["source_id"] == "bbc_world"
        assert fixed[0]["claim"] == "Breaking"
        assert any(i["type"] == "fallback_claim_created" for i in issues)

    def test_partial_fix(self, two_sources):
        event = {"sources": two_sources, "headline": "Test"}
        ct = [
            {"claim": "valid", "source_id": "bbc_world", "support_type": "direct"},
            {"claim": "bad", "source_id": "missing", "support_type": "direct"},
        ]
        fixed, issues = verify_and_fix_claim_trace(ct, event)
        assert len(fixed) == 1
        assert fixed[0]["claim"] == "valid"


# ---------------------------------------------------------------------------
# derive_single_source_warning
# ---------------------------------------------------------------------------

class TestSingleSourceWarning:
    def test_single_source(self):
        assert derive_single_source_warning(1) is True

    def test_multiple_sources(self):
        assert derive_single_source_warning(2) is False
        assert derive_single_source_warning(5) is False

    def test_zero_sources(self):
        assert derive_single_source_warning(0) is False
