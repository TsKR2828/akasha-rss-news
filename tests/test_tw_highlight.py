"""Phase 2 — tw_highlight 單元測試。

對應規格 §6.3 / §6.4 與 §20.1 P0（tw_highlight=true 必有 reason）。
"""
from __future__ import annotations

import json

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


class TestMainUnderscoreFilter:
    """驗證 main() 在 articles 目錄含 _dedup_log.json 時可正常跑完 exit 0（CARD-02）。"""

    def test_main_skips_underscore_files(self, tmp_path, monkeypatch):
        """articles 目錄同時含 _dedup_log.json（list）與正常文章時，main() 返回 0。"""
        # 建立假 beats.yaml
        beats_yaml = tmp_path / "beats.yaml"
        beats_yaml.write_text(
            "tw_highlight:\n"
            "  positive_keywords: [Taiwan]\n"
            "  context_keywords: [semiconductor]\n"
            "  false_positive_review: []\n",
            encoding="utf-8",
        )

        # 建立日期目錄
        date_str = "2026-06-11"
        articles_dir = tmp_path / "articles" / date_str
        articles_dir.mkdir(parents=True)

        # 放一個正常文章 JSON
        normal_article = {
            "article_id": "a" * 64,
            "source_id": "test_src",
            "title": "Taiwan semiconductor news",
            "summary": "",
        }
        (articles_dir / "article_001.json").write_text(
            json.dumps(normal_article, ensure_ascii=False), encoding="utf-8"
        )

        # 放一個 _dedup_log.json（內容為 list，json.loads 後非 dict，原本會崩）
        (articles_dir / "_dedup_log.json").write_text(
            json.dumps([{"dropped": "x" * 64}], ensure_ascii=False), encoding="utf-8"
        )

        exit_code = tw_highlight.main([
            "--beats-config", str(beats_yaml),
            "--articles-base", str(tmp_path / "articles"),
            "--date", date_str,
            "--dry-run",
        ])
        assert exit_code == 0
