"""Phase 2 — tw_highlight 單元測試。

對應規格 §6.3 / §6.4 與 §20.1 P0（tw_highlight=true 必有 reason）。
"""
from __future__ import annotations

import pytest

from src import tw_highlight


TW_CONFIG = {
    "positive_keywords": ["Taiwan", "Taipei", "TSMC", "Taiwan Strait", "Taiwanese"],
    "context_keywords": ["semiconductor", "defense", "China", "chip", "election", "trade"],
    "false_positive_review": ["Taipei concert", "Taiwanese artist", "restaurant", "travel list"],
}


def _article(title: str = "", summary: str = "") -> dict:
    return {
        "article_id": "x" * 64,
        "source_id": "bbc_world",
        "title": title,
        "summary": summary,
    }


class TestPositiveDetection:
    def test_no_positive_keyword_returns_false(self):
        art = _article(title="Apple releases new iPhone")
        flag, reason, kws = tw_highlight.detect(art, TW_CONFIG)
        assert flag is False
        assert reason is None
        assert kws == []

    def test_positive_with_context_returns_true(self):
        art = _article(title="TSMC announces new semiconductor fab",
                       summary="Major impact on supply chain.")
        flag, reason, kws = tw_highlight.detect(art, TW_CONFIG)
        assert flag is True
        assert reason is not None
        assert "TSMC" in reason
        assert "TSMC" in kws
        assert "semiconductor" in kws

    def test_positive_without_context_returns_false(self):
        """順帶提一句台灣、無實質公共議題 → 不算 highlight。"""
        art = _article(title="Tourist visits Taiwan and Japan this summer")
        flag, reason, kws = tw_highlight.detect(art, TW_CONFIG)
        assert flag is False


class TestFalsePositive:
    def test_taipei_concert_without_context_filtered(self):
        """規格 §6.3 false_positive_review。"""
        art = _article(title="Pop star to perform Taipei concert next month")
        flag, _, _ = tw_highlight.detect(art, TW_CONFIG)
        assert flag is False

    def test_taipei_concert_with_context_still_filtered(self):
        """若 FP 樣式命中且沒有任何 context → 仍視為 FP。"""
        art = _article(title="Pop star to perform Taipei concert")
        flag, _, _ = tw_highlight.detect(art, TW_CONFIG)
        assert flag is False

    def test_restaurant_filtered(self):
        art = _article(title="New Taiwanese restaurant opens in Tokyo")
        flag, _, _ = tw_highlight.detect(art, TW_CONFIG)
        assert flag is False


class TestReasonAndKeywords:
    def test_reason_lists_primary_positive_first(self):
        art = _article(title="Taiwan election results affect semiconductor trade")
        flag, reason, kws = tw_highlight.detect(art, TW_CONFIG)
        assert flag is True
        assert reason.startswith("Mentions Taiwan")

    def test_keywords_unique_and_includes_both_types(self):
        art = _article(title="TSMC defense chip exports to China continue")
        flag, reason, kws = tw_highlight.detect(art, TW_CONFIG)
        assert flag is True
        assert "TSMC" in kws
        assert any(c in kws for c in ("defense", "chip", "China"))


class TestAnnotate:
    def test_annotate_does_not_mutate_input(self):
        art = _article(title="TSMC semiconductor news")
        result = tw_highlight.annotate(art, TW_CONFIG)
        assert "tw_highlight" not in art
        assert result["tw_highlight"] is True
        assert result["tw_highlight_reason"] is not None
        assert result["tw_highlight_keywords"]

    def test_annotate_negative_case(self):
        art = _article(title="Apple releases new iPhone")
        result = tw_highlight.annotate(art, TW_CONFIG)
        assert result["tw_highlight"] is False
        assert result["tw_highlight_reason"] is None
        assert result["tw_highlight_keywords"] == []
