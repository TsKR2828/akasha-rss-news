"""Phase 2 — dedup 單元測試。"""
from __future__ import annotations

import pytest

from src import dedup


def _article(aid: str, canonical: str = "", title: str = "x",
             source_id: str = "bbc_world") -> dict:
    return {
        "article_id": aid,
        "source_id": source_id,
        "canonical_url": canonical,
        "title": title,
    }


class TestNormalizeTitle:
    def test_lowercases_and_strips_punctuation(self):
        assert dedup.normalize_title("Hello, World!") == "hello world"

    def test_collapses_whitespace(self):
        assert dedup.normalize_title("  Multiple   spaces  ") == "multiple spaces"


class TestCanonicalUrlMatch:
    def test_same_canonical_url_dropped(self):
        a = _article("a" * 64, canonical="https://x.com/1", title="Title A")
        b = _article("b" * 64, canonical="https://x.com/1", title="Title B")
        unique, dropped = dedup.dedup_articles([a, b])
        assert len(unique) == 1
        assert unique[0]["article_id"] == a["article_id"]
        assert len(dropped) == 1
        assert dropped[0]["reason"] == "exact_canonical_url"
        assert dropped[0]["article_id"] == b["article_id"]
        assert dropped[0]["duplicate_of"] == a["article_id"]

    def test_different_canonical_urls_kept(self):
        a = _article("a" * 64, canonical="https://x.com/1", title="t")
        b = _article("b" * 64, canonical="https://x.com/2", title="t")
        unique, dropped = dedup.dedup_articles([a, b])
        # 兩篇 canonical 不同，但同源同標題 → 仍會被 same_source_similar_title 砍
        # 為了專測 canonical URL，把標題稍微改一下
        b["title"] = "Completely different headline about world events"
        unique, dropped = dedup.dedup_articles([a, b])
        assert len(unique) == 2

    def test_empty_canonical_does_not_match_other_empty(self):
        a = _article("a" * 64, canonical="", title="apple news today")
        b = _article("b" * 64, canonical="", title="banana news today")
        unique, dropped = dedup.dedup_articles([a, b])
        assert len(unique) == 2


class TestSimilarTitleSameSource:
    def test_identical_title_same_source_dropped(self):
        a = _article("a" * 64, canonical="https://x.com/1",
                     title="Major summit announced today", source_id="bbc_world")
        b = _article("b" * 64, canonical="https://x.com/2",
                     title="Major summit announced today", source_id="bbc_world")
        unique, dropped = dedup.dedup_articles([a, b])
        assert len(unique) == 1
        assert dropped[0]["reason"] == "same_source_similar_title"

    def test_similar_title_different_source_kept(self):
        """跨源同標題不在本層處理，交給 event_cluster。"""
        a = _article("a" * 64, canonical="https://x.com/1",
                     title="Major summit announced today", source_id="bbc_world")
        b = _article("b" * 64, canonical="https://reuters.com/2",
                     title="Major summit announced today", source_id="reuters_world")
        unique, dropped = dedup.dedup_articles([a, b])
        assert len(unique) == 2


class TestPreservesOrder:
    def test_first_seen_wins(self):
        a = _article("a" * 64, canonical="https://x.com/1", title="t")
        b = _article("b" * 64, canonical="https://x.com/1", title="t")
        c = _article("c" * 64, canonical="https://x.com/1", title="t")
        unique, dropped = dedup.dedup_articles([a, b, c])
        assert len(unique) == 1
        assert unique[0]["article_id"] == a["article_id"]
        assert {d["article_id"] for d in dropped} == {b["article_id"], c["article_id"]}


class TestEmpty:
    def test_empty_input(self):
        unique, dropped = dedup.dedup_articles([])
        assert unique == []
        assert dropped == []
