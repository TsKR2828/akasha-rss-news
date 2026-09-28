"""2026-09-26 改善研究修正的回歸測試。

對應改善報告 Desktop/Claude/akasha-rss-news-improvement-2026-09-26.md：
- S0-1 claim_trace 初稿只放來源清單內的文章（QUAL-4）
- S0-2 媒體歸戶：同一家媒體多頻道不算多方確認（SRC-1/SEL-1）
- SEL-1 聚類去掉「 - reuters.com」後綴
- SEL-7 關鍵字整字比對
- CODE-3 驗證碼頁不算抓取成功
- 本機降成備援：pipeline --cloud-first 逐源合併
- GAP-1 本機抓取只自動合併 data/raw/
- 內容檢查（只警告）
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pytest

from src import content_check, event_cluster, fetch_rss, pipeline
from src.outlets import distinct_outlets, outlet_count, outlet_of
from src.textmatch import any_term, contains_term, count_terms

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import local_fetch  # noqa: E402


# ---------------------------------------------------------------------------
# outlets
# ---------------------------------------------------------------------------

class TestOutlets:
    @pytest.mark.parametrize("sid,expected", [
        ("guardian_books", "guardian"),
        ("reuters_world_google_news", "reuters"),
        ("reuters_business_google_news", "reuters"),
        ("nyt_arts", "nyt"),
        ("bbc_world", "bbc"),
        ("archdaily", "archdaily"),
        ("the_verge", "the_verge"),
    ])
    def test_outlet_of(self, sid, expected):
        assert outlet_of(sid) == expected

    def test_distinct_outlets(self):
        sources = [{"source_id": "guardian_books"}, {"source_id": "guardian_culture"},
                   {"source_id": "nyt_arts"}]
        assert distinct_outlets(sources) == {"guardian", "nyt"}
        assert outlet_count(sources) == 2


# ---------------------------------------------------------------------------
# textmatch
# ---------------------------------------------------------------------------

class TestTextMatch:
    @pytest.mark.parametrize("text,term", [
        ("staten island ferry", "tate"),
        ("senator warren said", "nato"),
        ("senator warren said", "war"),
        ("prince harry returns to british soil", "oil"),
        ("he said again", "ai"),
    ])
    def test_substring_no_longer_matches(self, text, term):
        assert not contains_term(text, term)

    @pytest.mark.parametrize("text,term", [
        ("new tariffs on steel", "tariff"),
        ("the fed holds rates", "fed"),
        ("ai act passes", "ai"),
        ("oil prices rise", "oil"),
        ("un security council meets", "un security"),
    ])
    def test_whole_word_and_plural_match(self, text, term):
        assert contains_term(text, term)

    def test_chinese_substring(self):
        assert contains_term("台灣央行升息", "升息")
        assert any_term("台灣央行升息", ["降息", "升息"])
        assert count_terms("oil and gas tariffs", ["oil", "tariff", "gdp"]) == 2


# ---------------------------------------------------------------------------
# event_cluster
# ---------------------------------------------------------------------------

def _art(aid, sid, title, url, tier=1, beat="ECON", published="2026-09-25T01:00:00+08:00",
         summary=""):
    return {"article_id": aid, "source_id": sid, "title": title, "url": url,
            "canonical_url": url, "tier": tier, "beat": beat,
            "published_at": published, "summary": summary, "publisher": sid}


class TestEventCluster:
    def test_strip_outlet_suffix(self):
        assert event_cluster.strip_outlet_suffix(
            "Oil prices rise on Houthi attack - reuters.com") == "Oil prices rise on Houthi attack"
        assert event_cluster.strip_outlet_suffix("A - B test") == "A - B test"

    def test_reuters_suffix_not_shared_keyword(self):
        kws = event_cluster.article_keywords(
            {"title": "Airbus pitches Eurofighter - reuters.com", "summary": "x reuters.com"})
        assert "reuters" not in kws and "com" not in kws

    def test_claim_trace_only_listed_sources(self):
        """同頻道第二篇不在 sources → 也不該出現在 claim_trace 初稿。"""
        cluster = [
            _art("a1", "bbc_world", "Story one", "https://bbc/1"),
            _art("a2", "bbc_world", "Story one update", "https://bbc/2"),
            _art("a3", "npr_world", "Story one NPR", "https://npr/1"),
        ]
        evt = event_cluster.build_event(cluster, "daily_20260925_evt_001")
        source_urls = {s["url"] for s in evt["sources"]}
        assert {ct["source_url"] for ct in evt["claim_trace"]} == source_urls
        assert "https://bbc/2" not in source_urls

    def test_same_outlet_is_medium_and_single_source(self):
        cluster = [
            _art("a1", "reuters_world_google_news", "Oil up", "https://r/1"),
            _art("a2", "reuters_business_google_news", "FTSE down", "https://r/2"),
        ]
        evt = event_cluster.build_event(cluster, "daily_20260925_evt_001")
        assert evt["confidence"] == "medium"
        assert evt["single_source_warning"] is True

    def test_two_outlets_is_high(self):
        cluster = [
            _art("a1", "bbc_world", "Quake hits", "https://bbc/1"),
            _art("a2", "npr_world", "Quake hits city", "https://npr/1", tier=2),
        ]
        evt = event_cluster.build_event(cluster, "daily_20260925_evt_001")
        assert evt["confidence"] == "high"
        assert evt["single_source_warning"] is False


# ---------------------------------------------------------------------------
# fetch_rss：驗證碼頁
# ---------------------------------------------------------------------------

CAPTCHA_PAGE = b"<html><head><title>Just a moment...</title></head><body>captcha</body></html>"
VALID_FEED = (b'<?xml version="1.0"?><rss version="2.0"><channel><title>T</title>'
              b'<item><title>Hello</title><link>https://x/1</link></item></channel></rss>')
EMPTY_FEED = b'<?xml version="1.0"?><rss version="2.0"><channel><title>T</title></channel></rss>'


class _Resp:
    def __init__(self, status, content):
        self.status_code = status
        self.content = content

    def raise_for_status(self):
        pass


class _Session:
    def __init__(self, resp):
        self.resp = resp
        self.headers = {}
        self.calls = 0

    def get(self, url, timeout=None, verify=True):
        self.calls += 1
        return self.resp


class TestFeedContentCheck:
    def test_captcha_page_is_failure(self):
        assert fetch_rss.check_feed_content(CAPTCHA_PAGE) is not None

    def test_valid_feed_ok(self):
        assert fetch_rss.check_feed_content(VALID_FEED) is None

    def test_valid_empty_feed_is_not_failure(self):
        assert fetch_rss.check_feed_content(EMPTY_FEED) is None

    def test_fetch_one_marks_captcha_failed_without_retry(self):
        sess = _Session(_Resp(202, CAPTCHA_PAGE))
        result, raw = fetch_rss.fetch_one(
            {"source_id": "marktechpost", "url": "https://m/feed"}, session=sess, backoff_base=0)
        assert result.status == "failed"
        assert raw is None
        assert "not a valid RSS" in result.error
        assert sess.calls == 1


# ---------------------------------------------------------------------------
# pipeline --cloud-first
# ---------------------------------------------------------------------------

class TestCloudFirstFetch:
    def _setup(self, tmp_path, monkeypatch, cloud: dict[str, bytes | None]):
        """cloud: {source_id: bytes（成功）| None（失敗）}"""
        monkeypatch.setattr(pipeline, "PROJECT_ROOT", tmp_path)
        date = "2026-09-26"
        raw_dir = tmp_path / "data" / "raw" / date
        raw_dir.mkdir(parents=True)
        # 本機預抓：a 與 b
        (raw_dir / "src_a.xml").write_bytes(b"LOCAL-A")
        (raw_dir / "src_b.xml").write_bytes(b"LOCAL-B")
        (raw_dir / "feed_health.json").write_text(json.dumps([
            {"source_id": "src_a", "status": "ok", "items_found": 5},
            {"source_id": "src_b", "status": "ok", "items_found": 7},
        ]), encoding="utf-8")

        def fake_step(name, module, d, dry_run, extra_argv=None):
            out = Path(extra_argv[extra_argv.index("--out-base") + 1]) / d
            out.mkdir(parents=True, exist_ok=True)
            health = []
            for sid, content in cloud.items():
                if content is None:
                    health.append({"source_id": sid, "status": "failed", "error": "blocked"})
                else:
                    (out / f"{sid}.xml").write_bytes(content)
                    health.append({"source_id": sid, "status": "ok", "error": None})
            (out / "feed_health.json").write_text(json.dumps(health), encoding="utf-8")
            return 0, 0.1

        monkeypatch.setattr(pipeline, "_run_module_step", fake_step)
        return date, raw_dir

    def test_merges_per_source(self, tmp_path, monkeypatch):
        date, raw_dir = self._setup(tmp_path, monkeypatch, {
            "src_a": b"CLOUD-A",   # 雲端成功 → 用雲端
            "src_b": None,         # 雲端失敗、本機有 → 用本機
            "src_c": None,         # 兩邊都沒有 → 警告
        })
        rc, note, extra = pipeline._cloud_first_fetch(date)
        assert rc == 0
        assert (raw_dir / "src_a.xml").read_bytes() == b"CLOUD-A"
        assert (raw_dir / "src_b.xml").read_bytes() == b"LOCAL-B"
        assert not (raw_dir / "src_c.xml").exists()
        health = {h["source_id"]: h for h in
                  json.loads((raw_dir / "feed_health.json").read_text(encoding="utf-8"))}
        assert health["src_b"]["status"] == "ok"
        assert "local pre-fetched" in health["src_b"]["error"]
        assert health["src_c"]["status"] == "failed"
        warnings = json.loads((raw_dir / "fetch_warnings.json").read_text(encoding="utf-8"))
        assert [w["source_id"] for w in warnings] == ["src_c"]
        assert "cloud 1, local backup 1, missing 1" in note

    def test_no_local_and_all_cloud_failed_aborts(self, tmp_path, monkeypatch):
        date, raw_dir = self._setup(tmp_path, monkeypatch, {"src_x": None})
        for f in raw_dir.glob("*"):
            f.unlink()
        rc, _, _ = pipeline._cloud_first_fetch(date)
        assert rc == 2

    def test_run_pipeline_cloud_first_persists_warnings_for_formatter(self, tmp_path, monkeypatch):
        """兩段式：--cloud-first --until select 的警告寫進 run state。"""
        from unittest.mock import patch
        monkeypatch.setattr(pipeline, "PROJECT_ROOT", tmp_path)
        date = "2026-09-26"
        monkeypatch.setattr(pipeline, "_cloud_first_fetch",
                            lambda d: (0, "cloud-first: test", [{"type": "other", "message": "X"}]))
        mods = ["normalize", "classifier", "tw_highlight", "dedup", "event_cluster", "selector"]
        patches = [patch(f"src.pipeline.{m}.main", return_value=0) for m in mods]
        for p in patches:
            p.start()
        try:
            summary = pipeline.run_pipeline(date, cloud_first=True, until="select")
        finally:
            for p in patches:
                p.stop()
        assert summary["status"] == "ok"
        state = pipeline.read_pipeline_run_state(date)
        assert state["warnings"] == [{"type": "other", "message": "X"}]
        assert state["steps"][0]["note"] == "cloud-first: test"


# ---------------------------------------------------------------------------
# local_fetch：只自動合併資料
# ---------------------------------------------------------------------------

class TestLocalFetchGuard:
    def test_only_data_raw_is_auto_merged(self):
        paths = ["data/raw/2026-09-26/bbc_world.xml", "data/raw/2026-09-26/feed_health.json",
                 "src/pipeline.py", "scripts/local_fetch.py", "prompts/routine_prompt.md"]
        assert local_fetch.non_data_paths(paths) == [
            "src/pipeline.py", "scripts/local_fetch.py", "prompts/routine_prompt.md"]

    def test_data_only_passes(self):
        assert local_fetch.non_data_paths(["data/raw/2026-09-26/x.xml", ""]) == []


# ---------------------------------------------------------------------------
# content_check（只警告）
# ---------------------------------------------------------------------------

def _rewritten(**over):
    e = {
        "event_id": "daily_20260926_evt_001",
        "headline": "巴基斯坦空襲阿富汗",
        "context": "巴基斯坦說打擊了10個目標。",
        "thread_text": "巴基斯坦說打擊了10個目標。",
        "threads_text": "巴基斯坦說打擊了10個目標。",
        "voice_text": "巴基斯坦說打擊了10個目標。",
        "confidence": "medium",
        "sources": [{"source_id": "bbc_world", "url": "https://bbc/1",
                     "title": "Four civilians killed", "summary": "Pakistan says it struck 10 targets"}],
        "claim_trace": [{"claim": "x", "source_id": "bbc_world", "source_url": "https://bbc/1",
                         "support_type": "direct"}],
    }
    e.update(over)
    return e


class TestContentCheck:
    D = date(2026, 9, 26)

    def _types(self, event):
        return {i["type"] for i in content_check.check_event(event, self.D)}

    def test_clean_event_has_no_issues(self):
        assert content_check.check_event(_rewritten(), self.D) == []

    def test_untranslated_and_empty(self):
        t = self._types(_rewritten(headline="Four civilians killed", voice_text=""))
        assert {"untranslated", "empty_field"} <= t

    def test_filler_and_banned(self):
        t = self._types(_rewritten(voice_text="目前只有單一消息來源，受到矚目。"))
        assert {"filler_phrase", "banned_phrase"} <= t

    def test_trace_url_not_in_sources(self):
        ev = _rewritten(claim_trace=[{"claim": "x", "source_id": "bbc_world",
                                      "source_url": "https://www.bbc.co.uk", "support_type": "direct"}])
        assert "trace_url_mismatch" in self._types(ev)

    def test_number_not_in_source(self):
        ev = _rewritten(context="巴基斯坦說打擊了12個目標。")
        issues = content_check.check_event(ev, self.D)
        nums = [i for i in issues if i["type"] == "number_not_in_source"]
        assert nums and "12" in nums[0]["detail"]

    def test_dates_are_not_counted_as_numbers(self):
        ev = _rewritten(context="巴基斯坦9月24日說打擊了10個目標。")
        assert "number_not_in_source" not in self._types(ev)

    def test_weekday_mismatch(self):
        """09-21 館報「9月20日週六」：2026-09-20 其實是星期日。"""
        ev = _rewritten(context="胡塞在9月20日週六發射飛彈。")
        issues = [i for i in content_check.check_event(ev, date(2026, 9, 21))
                  if i["type"] == "weekday_mismatch"]
        assert issues and "星期日" in issues[0]["detail"]

    def test_confidence_overclaim(self):
        ev = _rewritten(confidence="high", sources=[
            {"source_id": "guardian_books", "url": "https://g/1", "title": "a", "summary": "10"},
            {"source_id": "guardian_culture", "url": "https://g/2", "title": "b", "summary": ""}],
            claim_trace=[])
        assert "confidence_overclaim" in self._types(ev)

    def test_write_content_check_file(self, tmp_path):
        res = content_check.write_content_check([_rewritten(voice_text="")], "2026-09-26", tmp_path)
        saved = json.loads((tmp_path / "_content_check.json").read_text(encoding="utf-8"))
        assert saved["mode"] == "warn_only"
        assert saved["summary"]["events_flagged"] == 1 == res["summary"]["events_flagged"]
