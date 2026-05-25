"""Tests for src/html_cleaner.py — HTML/script/tracking param cleaning."""
import pytest

from src.html_cleaner import clean_html, strip_tracking_params, clean_article_for_rewrite, TRACKING_PARAMS
from src.normalize import TRACKING_PARAMS as NORMALIZE_TRACKING_PARAMS


# ---------------------------------------------------------------------------
# strip_tracking_params
# ---------------------------------------------------------------------------

class TestTrackingParamsSingleSource:
    """HIGH #2: html_cleaner must use the same TRACKING_PARAMS as normalize."""

    def test_same_object(self):
        assert TRACKING_PARAMS is NORMALIZE_TRACKING_PARAMS


class TestStripTrackingParams:
    def test_removes_utm_params(self):
        url = "https://example.com/article?utm_source=rss&utm_medium=feed&id=123"
        result = strip_tracking_params(url)
        assert "utm_source" not in result
        assert "utm_medium" not in result
        assert "id=123" in result

    def test_removes_fbclid(self):
        url = "https://example.com/page?fbclid=abc123&title=hello"
        result = strip_tracking_params(url)
        assert "fbclid" not in result
        assert "title=hello" in result

    def test_removes_bbc_tracking(self):
        url = "https://bbc.com/news/123?at_medium=RSS&at_campaign=rss"
        result = strip_tracking_params(url)
        assert "at_medium" not in result
        assert "at_campaign" not in result

    def test_preserves_clean_url(self):
        url = "https://example.com/article/2026/good-news"
        assert strip_tracking_params(url) == url

    def test_removes_fragment(self):
        url = "https://example.com/page#section1"
        result = strip_tracking_params(url)
        assert "#" not in result

    def test_handles_empty(self):
        assert strip_tracking_params("") == ""

    def test_handles_invalid_url(self):
        assert strip_tracking_params("not a url") == "not a url"


# ---------------------------------------------------------------------------
# clean_html
# ---------------------------------------------------------------------------

class TestCleanHtml:
    def test_strips_tags(self):
        assert clean_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_strips_script(self):
        html = "Before<script>alert('xss')</script>After"
        assert clean_html(html) == "Before After"

    def test_strips_style(self):
        html = "Before<style>.red{color:red}</style>After"
        assert clean_html(html) == "Before After"

    def test_decodes_entities(self):
        assert clean_html("Tom &amp; Jerry") == "Tom & Jerry"
        assert clean_html("&lt;tag&gt;") == "<tag>"
        assert clean_html("She said &ldquo;hi&rdquo;") == 'She said “hi”'

    def test_decodes_numeric_entities(self):
        assert clean_html("&#169;") == "©"
        assert clean_html("&#x2603;") == "☃"

    def test_collapses_whitespace(self):
        assert clean_html("  hello   world  ") == "hello world"
        assert clean_html("line1\n\n  line2") == "line1 line2"

    def test_empty_input(self):
        assert clean_html("") == ""
        assert clean_html(None) == ""

    def test_plain_text_passthrough(self):
        text = "This is just plain text with no HTML."
        assert clean_html(text) == text

    def test_cleans_urls_in_text(self):
        text = "Visit https://example.com/page?utm_source=rss&id=5 for details"
        result = clean_html(text)
        assert "utm_source" not in result
        assert "id=5" in result

    def test_complex_html(self):
        html = """
        <div class="article">
          <h1>Breaking News</h1>
          <p>Something <em>important</em> happened.</p>
          <script>trackEvent('view')</script>
          <style>.hide{display:none}</style>
          <a href="https://example.com">Link</a>
        </div>
        """
        result = clean_html(html)
        assert "Breaking News" in result
        assert "important" in result
        assert "trackEvent" not in result
        assert ".hide" not in result
        assert "<" not in result


# ---------------------------------------------------------------------------
# clean_article_for_rewrite
# ---------------------------------------------------------------------------

class TestCleanArticleForRewrite:
    def test_cleans_title_and_summary(self):
        article = {
            "title": "<b>Bold Title</b>",
            "summary": "<p>A summary with &amp; entities</p>",
            "url": "https://example.com/art?utm_source=rss",
            "source_id": "test",
        }
        result = clean_article_for_rewrite(article)
        assert result["title"] == "Bold Title"
        assert result["summary"] == "A summary with & entities"
        assert "utm_source" not in result["url"]
        assert result["source_id"] == "test"  # 非清理欄位不動

    def test_preserves_missing_fields(self):
        article = {"source_id": "test", "title": "Clean"}
        result = clean_article_for_rewrite(article)
        assert result["title"] == "Clean"
        assert "summary" not in result

    def test_does_not_mutate_original(self):
        article = {"title": "<b>HTML</b>", "summary": "ok"}
        clean_article_for_rewrite(article)
        assert article["title"] == "<b>HTML</b>"  # 原始沒被改
