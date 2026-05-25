"""Phase 1 — normalize unit tests.

驗收（規格 §5.3 / §20.1 P0）：
- normalize 結果通過 article.schema.json
- article_id = sha256(source_id + canonical_url) 重跑得到相同 ID
- canonicalize_url 去除追蹤參數
- fetch_window 過濾掉 24h+grace 之外的舊文
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from src import normalize


TAIPEI = timezone(timedelta(hours=8))

SAMPLE_SOURCE = {
    "source_id": "bbc_world",
    "name": "BBC World",
    "publisher": "BBC",
    "tier": 1,
    "beats": ["INTL"],
    "lang": "en",
}


def _xml_with_pubdate(pubdate: str, url: str = "https://www.bbc.com/news/world-12345") -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Sample</title>
    <item>
      <title>Sample Article</title>
      <link>{url}</link>
      <description>Sample summary.</description>
      <pubDate>{pubdate}</pubDate>
    </item>
  </channel>
</rss>
""".encode("utf-8")


SAMPLE_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Sample BBC World</title>
    <item>
      <title>Sample Article One</title>
      <link>https://www.bbc.com/news/world-12345</link>
      <description>Sample summary one.</description>
      <pubDate>Mon, 18 May 2026 01:20:00 +0000</pubDate>
    </item>
    <item>
      <title>Sample Article Two</title>
      <link>https://www.bbc.com/news/world-67890?utm_source=rss&amp;id=2</link>
      <description>Sample summary two.</description>
      <pubDate>Mon, 18 May 2026 02:30:00 +0000</pubDate>
    </item>
  </channel>
</rss>
"""


# ---------------------------------------------------------------------------
# URL canonicalization
# ---------------------------------------------------------------------------

class TestCanonicalizeUrl:
    def test_strips_utm_keeps_real_query(self):
        result = normalize.canonicalize_url("https://x.com/a?utm_source=rss&id=1")
        assert "utm_source" not in result
        assert "id=1" in result

    def test_strips_multiple_trackers(self):
        url = "https://x.com/a?utm_source=rss&fbclid=abc&id=1&gclid=xyz&mc_cid=qq"
        result = normalize.canonicalize_url(url)
        for bad in ("utm_source", "fbclid", "gclid", "mc_cid"):
            assert bad not in result
        assert "id=1" in result

    def test_lowercases_scheme_and_host(self):
        assert normalize.canonicalize_url("HTTPS://Example.COM/Path") == "https://example.com/Path"

    def test_empty_url_returns_empty(self):
        assert normalize.canonicalize_url("") == ""

    def test_no_query_unchanged(self):
        assert normalize.canonicalize_url("https://x.com/a") == "https://x.com/a"

    def test_strips_bbc_at_params(self):
        url = "https://bbc.com/news/123?at_medium=RSS&at_campaign=rss"
        result = normalize.canonicalize_url(url)
        assert "at_medium" not in result
        assert "at_campaign" not in result

    def test_strips_traffic_source(self):
        url = "https://www.aljazeera.com/economy/2026/article?traffic_source=rss"
        result = normalize.canonicalize_url(url)
        assert "traffic_source" not in result

    def test_strips_bbc_ns_params(self):
        url = "https://bbc.com/news/123?ns_mchannel=social&ns_source=twitter&ns_campaign=share"
        result = normalize.canonicalize_url(url)
        for param in ("ns_mchannel", "ns_source", "ns_campaign"):
            assert param not in result

    def test_strips_extended_click_ids(self):
        url = "https://x.com/a?gclsrc=aw.ds&dclid=abc&gbraid=xx&wbraid=yy&msclkid=zz"
        result = normalize.canonicalize_url(url)
        for param in ("gclsrc", "dclid", "gbraid", "wbraid", "msclkid"):
            assert param not in result


# ---------------------------------------------------------------------------
# article_id 必須穩定
# ---------------------------------------------------------------------------

class TestComputeArticleId:
    def test_format_is_64_hex(self):
        aid = normalize.compute_article_id("bbc_world", "https://x.com/a")
        assert len(aid) == 64
        assert all(c in "0123456789abcdef" for c in aid)

    def test_stable_across_calls(self):
        """規格 §20.1 P0: 重跑必須得到相同 article_id。"""
        a = normalize.compute_article_id("bbc_world", "https://x.com/a")
        b = normalize.compute_article_id("bbc_world", "https://x.com/a")
        assert a == b

    def test_different_for_different_sources(self):
        a = normalize.compute_article_id("bbc_world", "https://x.com/a")
        b = normalize.compute_article_id("reuters_world", "https://x.com/a")
        assert a != b

    def test_different_for_different_urls(self):
        a = normalize.compute_article_id("bbc_world", "https://x.com/a")
        b = normalize.compute_article_id("bbc_world", "https://x.com/b")
        assert a != b

    def test_tracking_params_dont_affect_id(self):
        """加上 utm_source 不會產生新 article_id。"""
        url_clean = "https://x.com/a"
        url_dirty = "https://x.com/a?utm_source=rss"
        a = normalize.compute_article_id("bbc_world", normalize.canonicalize_url(url_clean))
        b = normalize.compute_article_id("bbc_world", normalize.canonicalize_url(url_dirty))
        assert a == b


# ---------------------------------------------------------------------------
# parse_published / fetch_window
# ---------------------------------------------------------------------------

class TestTimeWindow:
    def test_window_calculation(self):
        ws = normalize.fetch_window_start("2026-05-18", default_hours=24, grace_hours=3)
        # 2026-05-18 05:00 +08:00 - 27h = 2026-05-17 02:00 +08:00
        assert ws == datetime(2026, 5, 17, 2, 0, tzinfo=TAIPEI)

    def test_article_in_window_passes(self, tmp_path):
        xml = _xml_with_pubdate("Mon, 18 May 2026 01:20:00 +0000")
        xml_path = tmp_path / "in.xml"
        xml_path.write_bytes(xml)
        window = normalize.fetch_window_start("2026-05-18")
        articles, found = normalize.normalize_source(
            SAMPLE_SOURCE, xml_path, "2026-05-18T05:00:00+08:00", window,
        )
        assert found == 1
        assert len(articles) == 1

    def test_old_article_excluded(self, tmp_path):
        # 8 天前的文章 → 排除
        xml = _xml_with_pubdate("Sat, 10 May 2026 00:00:00 +0000")
        xml_path = tmp_path / "old.xml"
        xml_path.write_bytes(xml)
        window = normalize.fetch_window_start("2026-05-18")
        articles, found = normalize.normalize_source(
            SAMPLE_SOURCE, xml_path, "2026-05-18T05:00:00+08:00", window,
        )
        assert found == 1
        assert articles == []


# ---------------------------------------------------------------------------
# normalize_entry / normalize_source
# ---------------------------------------------------------------------------

class TestNormalizeEntry:
    def _parse(self, xml: bytes = SAMPLE_XML):
        import feedparser
        return feedparser.parse(xml)

    def test_returns_normalized_dict(self):
        feed = self._parse()
        article = normalize.normalize_entry(
            feed.entries[0], SAMPLE_SOURCE, "2026-05-18T05:00:00+08:00",
        )
        assert article is not None
        assert article["source_id"] == "bbc_world"
        assert article["title"] == "Sample Article One"
        assert article["url"] == "https://www.bbc.com/news/world-12345"
        assert article["beat_candidates"] == ["INTL"]
        assert article["lang"] == "en"

    def test_tracking_params_stripped_in_canonical_url(self):
        feed = self._parse()
        article = normalize.normalize_entry(
            feed.entries[1], SAMPLE_SOURCE, "2026-05-18T05:00:00+08:00",
        )
        assert "utm_source" not in article["canonical_url"]
        # 但 original url 保留追蹤參數
        assert "utm_source" in article["url"]

    def test_article_id_stable_across_parses(self):
        """重新 fetch、重新 parse 必須產出相同 article_id。"""
        f1 = self._parse()
        f2 = self._parse()
        a = normalize.normalize_entry(f1.entries[0], SAMPLE_SOURCE, "2026-05-18T05:00:00+08:00")
        b = normalize.normalize_entry(f2.entries[0], SAMPLE_SOURCE, "2026-05-19T05:00:00+08:00")
        assert a["article_id"] == b["article_id"]

    def test_missing_title_returns_none(self):
        xml = b"""<?xml version="1.0"?><rss version="2.0"><channel>
          <item><link>https://x.com/a</link>
          <pubDate>Mon, 18 May 2026 01:20:00 +0000</pubDate></item>
        </channel></rss>"""
        feed = self._parse(xml)
        article = normalize.normalize_entry(feed.entries[0], SAMPLE_SOURCE, "")
        assert article is None

    def test_missing_pubdate_returns_none(self):
        xml = b"""<?xml version="1.0"?><rss version="2.0"><channel>
          <item><title>x</title><link>https://x.com/a</link></item>
        </channel></rss>"""
        feed = self._parse(xml)
        article = normalize.normalize_entry(feed.entries[0], SAMPLE_SOURCE, "")
        assert article is None

    def test_summary_html_stripped(self):
        """MEDIUM #4: summary 中的 HTML 標籤必須在 normalize 時清掉。"""
        xml = b"""<?xml version="1.0"?><rss version="2.0"><channel>
          <item>
            <title>Test</title>
            <link>https://x.com/a</link>
            <description>&lt;p&gt;Hello &lt;b&gt;world&lt;/b&gt;&lt;/p&gt;</description>
            <pubDate>Mon, 18 May 2026 01:20:00 +0000</pubDate>
          </item>
        </channel></rss>"""
        feed = self._parse(xml)
        article = normalize.normalize_entry(feed.entries[0], SAMPLE_SOURCE, "")
        assert "<" not in article["summary"]
        assert "Hello" in article["summary"]
        assert "world" in article["summary"]

    def test_summary_none_stays_none(self):
        """summary 為 None 時不該 crash。"""
        xml = b"""<?xml version="1.0"?><rss version="2.0"><channel>
          <item>
            <title>Test</title>
            <link>https://x.com/a</link>
            <pubDate>Mon, 18 May 2026 01:20:00 +0000</pubDate>
          </item>
        </channel></rss>"""
        feed = self._parse(xml)
        article = normalize.normalize_entry(feed.entries[0], SAMPLE_SOURCE, "")
        assert article is not None


# ---------------------------------------------------------------------------
# 規格 §17 schema 驗證 — 跨檢查 normalize 輸出 vs article.schema.json
# ---------------------------------------------------------------------------

class TestArticleSchemaConformance:
    def test_normalized_articles_pass_schema(self, article_schema, tmp_path):
        xml_path = tmp_path / "sample.xml"
        xml_path.write_bytes(SAMPLE_XML)
        # 用足夠寬的時間窗口讓兩篇都入選
        window = datetime(2026, 5, 1, tzinfo=TAIPEI)
        articles, found = normalize.normalize_source(
            SAMPLE_SOURCE, xml_path, "2026-05-18T05:00:00+08:00", window,
        )
        assert found == 2
        assert len(articles) == 2
        validator = Draft7Validator(article_schema)
        for art in articles:
            validator.validate(art)  # 任一失敗會 raise

    def test_normalized_article_id_format_matches_schema_pattern(self, article_schema, tmp_path):
        xml_path = tmp_path / "sample.xml"
        xml_path.write_bytes(SAMPLE_XML)
        window = datetime(2026, 5, 1, tzinfo=TAIPEI)
        articles, _ = normalize.normalize_source(
            SAMPLE_SOURCE, xml_path, "2026-05-18T05:00:00+08:00", window,
        )
        for art in articles:
            assert len(art["article_id"]) == 64
            assert all(c in "0123456789abcdef" for c in art["article_id"])
