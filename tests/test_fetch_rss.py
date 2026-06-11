"""Phase 1 — fetch_rss unit tests.

驗收（規格 §4 / §20.1 P0）：
- 單一 source 失敗 → continue_with_warning（status: partial、warnings 有條目）
- 全部 source 失敗 → abort_report（status: failed、不產出假成功）
- 連續失敗 3 次的 source 觸發告警
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src import fetch_rss


SAMPLE_SOURCE = {
    "source_id": "bbc_world",
    "name": "BBC World",
    "publisher": "BBC",
    "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "beats": ["INTL"],
    "lang": "en",
    "tier": 1,
    "transport": "direct_rss",
    "is_proxy": False,
    "enabled": True,
}


def _mock_response(status: int = 200, content: bytes = b"<rss></rss>") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.content = content
    if status >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(f"{status}")
    else:
        resp.raise_for_status.return_value = None
    return resp


# ---------------------------------------------------------------------------
# fetch_one
# ---------------------------------------------------------------------------

class TestFetchOne:
    def test_success(self):
        sess = MagicMock()
        sess.headers = {}
        sess.get.return_value = _mock_response(200, b"<rss>OK</rss>")
        result, raw = fetch_rss.fetch_one(SAMPLE_SOURCE, timeout=1, retries=0, session=sess)
        assert result.status == "ok"
        assert result.http_status == 200
        assert raw == b"<rss>OK</rss>"

    def test_http_500_retries_then_fails(self):
        sess = MagicMock()
        sess.headers = {}
        sess.get.return_value = _mock_response(500)
        result, raw = fetch_rss.fetch_one(
            SAMPLE_SOURCE, timeout=1, retries=2, backoff_base=0.0, session=sess,
        )
        assert result.status == "failed"
        assert result.http_status == 500
        assert raw is None
        # 1 initial + 2 retries
        assert sess.get.call_count == 3

    def test_timeout_returns_failed(self):
        sess = MagicMock()
        sess.headers = {}
        sess.get.side_effect = requests.Timeout("timed out")
        result, raw = fetch_rss.fetch_one(
            SAMPLE_SOURCE, timeout=1, retries=0, backoff_base=0.0, session=sess,
        )
        assert result.status == "failed"
        assert result.error is not None
        assert "timed out" in result.error.lower() or "timeout" in result.error.lower()
        assert raw is None

    def test_connection_error_returns_failed(self):
        sess = MagicMock()
        sess.headers = {}
        sess.get.side_effect = requests.ConnectionError("name resolution failed")
        result, raw = fetch_rss.fetch_one(
            SAMPLE_SOURCE, timeout=1, retries=0, backoff_base=0.0, session=sess,
        )
        assert result.status == "failed"
        assert raw is None


# ---------------------------------------------------------------------------
# decide_overall_status — 規格 §4.2 fail_mode
# ---------------------------------------------------------------------------

class TestDecideOverallStatus:
    def _result(self, sid: str, status: str = "ok", consecutive: int = 0) -> fetch_rss.FetchResult:
        return fetch_rss.FetchResult(
            source_id=sid, status=status, consecutive_failures=consecutive,
        )

    def test_all_ok_returns_ok(self):
        sources = [{"source_id": "a", "enabled": True}, {"source_id": "b", "enabled": True}]
        results = [self._result("a"), self._result("b")]
        status, warnings = fetch_rss.decide_overall_status(results, sources)
        assert status == "ok"
        assert warnings == []

    def test_single_failure_returns_partial_with_warning(self):
        """規格 §4.2: single_source_failed → continue_with_warning。"""
        sources = [{"source_id": "a", "enabled": True}, {"source_id": "b", "enabled": True}]
        results = [self._result("a"), self._result("b", "failed")]
        status, warnings = fetch_rss.decide_overall_status(results, sources)
        assert status == "partial"
        source_failed_warnings = [w for w in warnings if w["type"] == "source_failed"]
        assert len(source_failed_warnings) == 1
        assert source_failed_warnings[0]["source_id"] == "b"

    def test_all_failed_returns_failed_with_abort_warning(self):
        """規格 §4.2: all_sources_failed → abort_report，不產出假成功。"""
        sources = [{"source_id": "a", "enabled": True}, {"source_id": "b", "enabled": True}]
        results = [self._result("a", "failed"), self._result("b", "failed")]
        status, warnings = fetch_rss.decide_overall_status(results, sources)
        assert status == "failed"
        # 至少一則 warning 提到「aborting」或「all」
        assert any(
            ("abort" in w["message"].lower() or "all" in w["message"].lower())
            for w in warnings
        )

    def test_consecutive_failures_triggers_alert(self):
        """規格 §4.1: 連續失敗 3 次的 source 必須在 warnings 中出現告警。"""
        sources = [{"source_id": "a", "enabled": True}, {"source_id": "b", "enabled": True}]
        # a 成功，b 失敗且累計 3 次
        results = [self._result("a"), self._result("b", "failed", consecutive=3)]
        status, warnings = fetch_rss.decide_overall_status(results, sources, alert_after=3)
        # 應該有 source_failed (本次失敗) + 連續失敗告警
        b_warnings = [w for w in warnings if w["source_id"] == "b"]
        assert len(b_warnings) >= 2
        assert any("3 times" in w["message"] for w in b_warnings)


# ---------------------------------------------------------------------------
# State persistence — consecutive_failures 跨次累計
# ---------------------------------------------------------------------------

class TestConsecutiveFailureState:
    def test_state_increments_across_runs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fetch_rss, "STATE_FILE", tmp_path / "state.json")

        def fail_once(source, *a, **kw):
            return (
                fetch_rss.FetchResult(
                    source_id=source["source_id"], status="failed", error="boom",
                ),
                None,
            )

        with patch.object(fetch_rss, "fetch_one", side_effect=fail_once):
            _, state = fetch_rss.fetch_all([SAMPLE_SOURCE])
            assert state["bbc_world"] == 1
            _, state = fetch_rss.fetch_all([SAMPLE_SOURCE])
            assert state["bbc_world"] == 2
            _, state = fetch_rss.fetch_all([SAMPLE_SOURCE])
            assert state["bbc_world"] == 3

    def test_state_resets_on_success(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fetch_rss, "STATE_FILE", tmp_path / "state.json")
        fetch_rss.save_state({"bbc_world": 2})

        def ok(source, *a, **kw):
            return (
                fetch_rss.FetchResult(source_id=source["source_id"], status="ok"),
                b"<rss/>",
            )

        with patch.object(fetch_rss, "fetch_one", side_effect=ok):
            _, state = fetch_rss.fetch_all([SAMPLE_SOURCE])
        assert state["bbc_world"] == 0


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

class TestIO:
    def test_write_raw_creates_file(self, tmp_path):
        path = fetch_rss.write_raw(tmp_path / "raw", "bbc_world", b"<rss/>")
        assert path.exists()
        assert path.read_bytes() == b"<rss/>"

    def test_write_health_log_format(self, tmp_path):
        results = [
            fetch_rss.FetchResult(
                source_id="bbc_world", status="ok", http_status=200,
                fetched_at="2026-05-18T05:01:00+08:00", items_found=25,
            ),
            fetch_rss.FetchResult(
                source_id="failing", status="failed", error="boom",
                consecutive_failures=2,
            ),
        ]
        path = fetch_rss.write_health_log(tmp_path / "raw", results)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data) == 2
        assert data[0]["source_id"] == "bbc_world"
        assert data[0]["status"] == "ok"
        assert data[1]["status"] == "failed"
        assert data[1]["consecutive_failures"] == 2

    def test_write_warnings_log_creates_file(self, tmp_path):
        warnings = [
            {"type": "source_failed", "source_id": "bbc_world", "message": "bbc_world failed: boom"},
        ]
        path = fetch_rss.write_warnings_log(tmp_path / "raw", warnings)
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data == warnings

    def test_write_warnings_log_empty_list(self, tmp_path):
        path = fetch_rss.write_warnings_log(tmp_path / "raw", [])
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data == []


# ---------------------------------------------------------------------------
# main() — fetch_warnings.json 落地
# ---------------------------------------------------------------------------

MINIMAL_FEEDS_YAML = """\
sources:
  - source_id: src_ok
    name: OK Source
    publisher: Test
    url: http://example.com/ok.xml
    beats: []
    lang: en
    tier: 1
    transport: direct_rss
    is_proxy: false
    enabled: true
  - source_id: src_fail
    name: Fail Source
    publisher: Test
    url: http://example.com/fail.xml
    beats: []
    lang: en
    tier: 1
    transport: direct_rss
    is_proxy: false
    enabled: true
"""

MINIMAL_FEEDS_ONE_YAML = """\
sources:
  - source_id: src_ok
    name: OK Source
    publisher: Test
    url: http://example.com/ok.xml
    beats: []
    lang: en
    tier: 1
    transport: direct_rss
    is_proxy: false
    enabled: true
"""


class TestMainWarningsLog:
    """驗證 main() 在執行後把 warnings 寫入 fetch_warnings.json。"""

    def _make_feeds_file(self, tmp_path: Path, content: str) -> Path:
        feeds_file = tmp_path / "feeds.yaml"
        feeds_file.write_text(content, encoding="utf-8")
        return feeds_file

    def test_one_source_failed_writes_source_failed_entry(self, tmp_path, monkeypatch):
        """一源失敗時 fetch_warnings.json 必須含 source_failed 條目。"""
        monkeypatch.setattr(fetch_rss, "STATE_FILE", tmp_path / "state.json")
        feeds_file = self._make_feeds_file(tmp_path, MINIMAL_FEEDS_YAML)
        out_base = tmp_path / "raw"

        def fake_fetch_one(source, *a, **kw):
            if source["source_id"] == "src_fail":
                return (
                    fetch_rss.FetchResult(
                        source_id="src_fail", status="failed", error="connection error",
                    ),
                    None,
                )
            return (
                fetch_rss.FetchResult(source_id=source["source_id"], status="ok"),
                b"<rss/>",
            )

        with patch.object(fetch_rss, "fetch_one", side_effect=fake_fetch_one):
            rc = fetch_rss.main([
                "--feeds", str(feeds_file),
                "--out-base", str(out_base),
                "--date", "2026-01-01",
            ])

        assert rc == 0  # partial → continue_with_warning
        warnings_path = out_base / "2026-01-01" / "fetch_warnings.json"
        assert warnings_path.exists(), "fetch_warnings.json 必須存在"
        data = json.loads(warnings_path.read_text(encoding="utf-8"))
        source_failed = [w for w in data if w.get("type") == "source_failed"]
        assert len(source_failed) >= 1
        assert any(w["source_id"] == "src_fail" for w in source_failed)

    def test_all_success_writes_empty_warnings(self, tmp_path, monkeypatch):
        """全部成功時 fetch_warnings.json 應寫出空 list。"""
        monkeypatch.setattr(fetch_rss, "STATE_FILE", tmp_path / "state.json")
        feeds_file = self._make_feeds_file(tmp_path, MINIMAL_FEEDS_ONE_YAML)
        out_base = tmp_path / "raw"

        def fake_fetch_one(source, *a, **kw):
            return (
                fetch_rss.FetchResult(source_id=source["source_id"], status="ok"),
                b"<rss/>",
            )

        with patch.object(fetch_rss, "fetch_one", side_effect=fake_fetch_one):
            rc = fetch_rss.main([
                "--feeds", str(feeds_file),
                "--out-base", str(out_base),
                "--date", "2026-01-01",
            ])

        assert rc == 0
        warnings_path = out_base / "2026-01-01" / "fetch_warnings.json"
        assert warnings_path.exists(), "fetch_warnings.json 即使空也必須存在"
        data = json.loads(warnings_path.read_text(encoding="utf-8"))
        assert data == []


# ---------------------------------------------------------------------------
# load_state — STATE_FILE 不存在時從歷史 feed_health.json 推導（CARD-07）
# ---------------------------------------------------------------------------

def _make_feed_health(date_dir: Path, records: list[dict]) -> None:
    """在 date_dir 下寫入 feed_health.json。"""
    date_dir.mkdir(parents=True, exist_ok=True)
    (date_dir / "feed_health.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


class TestLoadStateFromHistory:
    """STATE_FILE 不存在時，load_state 應從歷史 feed_health.json 推導 consecutive_failures。"""

    def test_consecutive_failures_derived_from_history(self, tmp_path, monkeypatch):
        """(a) state 檔不存在 + 某源連敗 3 天 → load_state 回傳 {源: 3}。"""
        monkeypatch.setattr(fetch_rss, "STATE_FILE", tmp_path / "nonexistent_state.json")
        raw_base = tmp_path / "raw"

        # 建立 3 個日期目錄，bbc_world 每天都 failed
        _make_feed_health(raw_base / "2026-06-09", [
            {"source_id": "bbc_world", "status": "failed"},
        ])
        _make_feed_health(raw_base / "2026-06-10", [
            {"source_id": "bbc_world", "status": "failed"},
        ])
        _make_feed_health(raw_base / "2026-06-11", [
            {"source_id": "bbc_world", "status": "failed"},
        ])

        state = fetch_rss.load_state(raw_base=raw_base)

        assert state.get("bbc_world") == 3, f"期望 bbc_world=3，實際 state={state}"

    def test_source_ok_on_latest_day_returns_zero_or_absent(self, tmp_path, monkeypatch):
        """(b) 最近一天 ok → 計數為 0 或不在 dict 中。"""
        monkeypatch.setattr(fetch_rss, "STATE_FILE", tmp_path / "nonexistent_state.json")
        raw_base = tmp_path / "raw"

        # 最舊兩天 failed，最新一天 ok
        _make_feed_health(raw_base / "2026-06-09", [
            {"source_id": "bbc_world", "status": "failed"},
        ])
        _make_feed_health(raw_base / "2026-06-10", [
            {"source_id": "bbc_world", "status": "failed"},
        ])
        _make_feed_health(raw_base / "2026-06-11", [
            {"source_id": "bbc_world", "status": "ok"},
        ])

        state = fetch_rss.load_state(raw_base=raw_base)

        # 最近一天 ok，連敗計數應為 0 或不在 dict
        count = state.get("bbc_world", 0)
        assert count == 0, f"最近一天 ok，期望 count=0，實際 state={state}"
