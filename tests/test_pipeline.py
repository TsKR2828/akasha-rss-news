"""Tests for src/pipeline.py — pipeline orchestrator."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline import (
    _collect_stats,
    _load_feeds_counts,
    _read_fetch_warnings,
    _read_selected_events,
    _run_module_step,
    _write_pipeline_run_state,
    read_pipeline_run_state,
    run_pipeline,
)


# ---------------------------------------------------------------------------
# _run_module_step
# ---------------------------------------------------------------------------

class TestRunModuleStep:
    def test_normal_exit(self):
        mod = MagicMock()
        mod.main.return_value = 0
        rc, dur = _run_module_step("test", mod, "2026-05-20", dry_run=False)
        assert rc == 0
        assert dur >= 0
        mod.main.assert_called_once_with(["--date", "2026-05-20"])

    def test_dry_run_passed_to_claude_rewrite(self):
        mod = MagicMock()
        mod.main.return_value = 0
        rc, _ = _run_module_step("claude_rewrite", mod, "2026-05-20", dry_run=True)
        assert rc == 0
        mod.main.assert_called_once_with(["--date", "2026-05-20", "--dry-run"])

    def test_dry_run_not_passed_to_other_steps(self):
        mod = MagicMock()
        mod.main.return_value = 0
        _run_module_step("normalize", mod, "2026-05-20", dry_run=True)
        mod.main.assert_called_once_with(["--date", "2026-05-20"])

    def test_exception_returns_99(self):
        mod = MagicMock()
        mod.main.side_effect = RuntimeError("boom")
        rc, _ = _run_module_step("test", mod, "2026-05-20", dry_run=False)
        assert rc == 99

    def test_system_exit_captured(self):
        mod = MagicMock()
        mod.main.side_effect = SystemExit(2)
        rc, _ = _run_module_step("test", mod, "2026-05-20", dry_run=False)
        assert rc == 2

    def test_system_exit_none_code(self):
        mod = MagicMock()
        mod.main.side_effect = SystemExit(None)
        rc, _ = _run_module_step("test", mod, "2026-05-20", dry_run=False)
        assert rc == 1


# ---------------------------------------------------------------------------
# _collect_stats
# ---------------------------------------------------------------------------

class TestCollectStats:
    def test_empty_dirs(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        stats = _collect_stats("2026-05-20")
        assert stats["total_feeds_checked"] == 0
        assert stats["total_articles_after_filter"] == 0
        assert stats["total_events_selected"] == 0

    def test_reads_health_log(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        raw_dir = tmp_path / "data" / "raw" / "2026-05-20"
        raw_dir.mkdir(parents=True)
        health = [
            {"source_id": "a", "status": "ok", "items_valid": 10},
            {"source_id": "b", "status": "failed", "items_valid": 0},
            {"source_id": "c", "status": "ok", "items_valid": 5},
        ]
        (raw_dir / "feed_health.json").write_text(json.dumps(health))

        stats = _collect_stats("2026-05-20")
        assert stats["total_feeds_checked"] == 3
        assert stats["total_feeds_failed"] == 1
        assert stats["total_feeds_failed_remote_blocked"] == 0  # no feeds.yaml in tmp → 0
        assert stats["total_articles_fetched"] == 15

    def test_counts_articles(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        art_dir = tmp_path / "data" / "articles" / "2026-05-20"
        art_dir.mkdir(parents=True)
        (art_dir / "abc123.json").write_text("{}")
        (art_dir / "def456.json").write_text("{}")
        (art_dir / "_dedup_log.json").write_text("[]")  # should be excluded

        stats = _collect_stats("2026-05-20")
        assert stats["total_articles_after_filter"] == 2

    def test_reads_manifest(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {
            "selected_event_ids": ["e1", "e2", "e3"],
            "dropped": [{"event_id": "e4"}, {"event_id": "e5"}],
        }
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))

        stats = _collect_stats("2026-05-20")
        assert stats["total_events_merged"] == 5
        assert stats["total_events_selected"] == 3


# ---------------------------------------------------------------------------
# _read_fetch_warnings（CARD-06）
# ---------------------------------------------------------------------------

class TestReadFetchWarnings:
    def test_no_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        result = _read_fetch_warnings("2026-05-20")
        assert result == []

    def test_filters_remote_blocked_source(self, tmp_path, monkeypatch):
        """remote_blocked 來源的 warning 應被過濾；真失敗來源應保留。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        # 建立 feeds.yaml，rb_src 是 remote_blocked
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True)
        feeds_yaml = (
            "sources:\n"
            "  - source_id: rb_src\n"
            "    remote_blocked: true\n"
            "  - source_id: real_fail_src\n"
            "    remote_blocked: false\n"
        )
        (config_dir / "feeds.yaml").write_text(feeds_yaml, encoding="utf-8")

        # 建立 fetch_warnings.json
        raw_dir = tmp_path / "data" / "raw" / "2026-05-20"
        raw_dir.mkdir(parents=True)
        warnings = [
            {"source_id": "rb_src", "type": "source_failed", "message": "remote blocked"},
            {"source_id": "real_fail_src", "type": "source_failed", "message": "真失敗"},
        ]
        (raw_dir / "fetch_warnings.json").write_text(
            json.dumps(warnings), encoding="utf-8"
        )

        result = _read_fetch_warnings("2026-05-20")
        assert len(result) == 1
        assert result[0]["source_id"] == "real_fail_src"

    def test_type_normalized_to_source_failed(self, tmp_path, monkeypatch):
        """fetch_warnings.json 中的 type 如果不是 source_failed，應被正規化。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        raw_dir = tmp_path / "data" / "raw" / "2026-05-20"
        raw_dir.mkdir(parents=True)
        warnings = [
            {"source_id": "some_src", "type": "other_type", "message": "異常"},
        ]
        (raw_dir / "fetch_warnings.json").write_text(
            json.dumps(warnings), encoding="utf-8"
        )

        result = _read_fetch_warnings("2026-05-20")
        assert len(result) == 1
        assert result[0]["type"] == "source_failed"


class TestRunPipelineFetchWarnings:
    """CARD-06：fetch warnings 併入 pipeline_warnings，過濾 remote_blocked。"""

    @staticmethod
    def _mock_all_modules():
        patches = {}
        for mod_name in [
            "src.pipeline.fetch_rss",
            "src.pipeline.normalize",
            "src.pipeline.classifier",
            "src.pipeline.tw_highlight",
            "src.pipeline.dedup",
            "src.pipeline.event_cluster",
            "src.pipeline.selector",
            "src.pipeline.claude_rewrite",
        ]:
            p = patch(f"{mod_name}.main", return_value=0)
            patches[mod_name] = p
        return patches

    def test_fetch_warning_real_fail_reaches_generate(self, tmp_path, monkeypatch):
        """raw 目錄有 fetch_warnings.json：1 個 remote_blocked 源 + 1 個真失敗源 →
        傳入 generate_all_outputs 的 pipeline_warnings 只含真失敗、report status partial。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        # 建立 feeds.yaml
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True)
        feeds_yaml = (
            "sources:\n"
            "  - source_id: rb_src\n"
            "    remote_blocked: true\n"
            "  - source_id: real_fail_src\n"
            "    remote_blocked: false\n"
        )
        (config_dir / "feeds.yaml").write_text(feeds_yaml, encoding="utf-8")

        # 建立 fetch_warnings.json
        raw_dir = tmp_path / "data" / "raw" / "2026-05-20"
        raw_dir.mkdir(parents=True)
        fetch_warnings_data = [
            {"source_id": "rb_src", "type": "source_failed", "message": "remote blocked"},
            {"source_id": "real_fail_src", "type": "source_failed", "message": "真失敗"},
        ]
        (raw_dir / "fetch_warnings.json").write_text(
            json.dumps(fetch_warnings_data), encoding="utf-8"
        )

        # 建立 events manifest
        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": [], "dropped": []}
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))

        patches = self._mock_all_modules()
        mocks = {k: p.start() for k, p in patches.items()}

        captured: list[list] = []

        def _fake_generate(*, pipeline_warnings, **kw):
            captured.append(list(pipeline_warnings))
            # warnings 非空 → partial
            status = "partial" if pipeline_warnings else "ok"
            return ({"status": status}, [])

        with patch("src.pipeline.generate_all_outputs", side_effect=_fake_generate):
            summary = run_pipeline("2026-05-20", dry_run=True, output_base=tmp_path / "out")

        for p in patches.values():
            p.stop()

        assert len(captured) == 1
        warnings_passed = captured[0]
        # 只有真失敗來源進報告
        assert len(warnings_passed) == 1
        assert warnings_passed[0]["source_id"] == "real_fail_src"
        assert warnings_passed[0]["type"] == "source_failed"
        assert summary["status"] == "partial"


# ---------------------------------------------------------------------------
# _read_selected_events
# ---------------------------------------------------------------------------

class TestReadSelectedEvents:
    def test_no_manifest(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        events, dropped, warnings = _read_selected_events("2026-05-20")
        assert events == []
        assert dropped == []
        assert warnings == []

    def test_reads_events_and_warnings(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)

        manifest = {
            "selected_event_ids": ["e1", "e2"],
            "dropped": [{"event_id": "e3", "drop_reason": "low_score"}],
        }
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))
        (evt_dir / "e1.json").write_text(json.dumps({"event_id": "e1", "beat": "INTL"}))
        (evt_dir / "e2.json").write_text(json.dumps({"event_id": "e2", "beat": "AI"}))

        rlog = {"lint_warnings": [{"type": "warn", "message": "test"}]}
        (evt_dir / "_rewrite_log.json").write_text(json.dumps(rlog))

        events, dropped, warnings = _read_selected_events("2026-05-20")
        assert len(events) == 2
        assert len(dropped) == 1
        assert len(warnings) == 1

    def test_missing_event_file_logged(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": ["missing"], "dropped": []}
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))

        events, _, _ = _read_selected_events("2026-05-20")
        assert events == []


# ---------------------------------------------------------------------------
# run_pipeline — integration with mocked modules
# ---------------------------------------------------------------------------

class TestRunPipeline:
    @staticmethod
    def _mock_all_modules():
        """Patch all pipeline module main() functions to return 0."""
        patches = {}
        for mod_name in [
            "src.pipeline.fetch_rss",
            "src.pipeline.normalize",
            "src.pipeline.classifier",
            "src.pipeline.tw_highlight",
            "src.pipeline.dedup",
            "src.pipeline.event_cluster",
            "src.pipeline.selector",
            "src.pipeline.claude_rewrite",
        ]:
            p = patch(f"{mod_name}.main", return_value=0)
            patches[mod_name] = p
        return patches

    def test_all_steps_success(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        mocks = {k: p.start() for k, p in patches.items()}

        # Set up minimal filesystem state for formatter
        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": [], "dropped": []}
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))

        with patch("src.pipeline.generate_all_outputs") as mock_fmt:
            mock_fmt.return_value = ({"status": "ok"}, [])
            summary = run_pipeline("2026-05-20", dry_run=True, output_base=tmp_path / "out")

        assert summary["status"] == "ok"
        assert len(summary["steps"]) == 9
        assert all(s["exit_code"] == 0 for s in summary["steps"])

        for p in patches.values():
            p.stop()

    def test_fetch_all_fail_aborts(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        mocks = {k: p.start() for k, p in patches.items()}
        mocks["src.pipeline.fetch_rss"].return_value = 2

        summary = run_pipeline("2026-05-20", dry_run=True)

        assert summary["status"] == "failed"
        assert summary["reason"] == "all_sources_failed"
        assert len(summary["steps"]) == 1
        assert summary["steps"][0]["name"] == "fetch_rss"

        # Subsequent modules should NOT have been called
        mocks["src.pipeline.normalize"].assert_not_called()

        for p in patches.values():
            p.stop()

    def test_partial_failure_continues(self, tmp_path, monkeypatch):
        """非關鍵步驟（tw_highlight）失敗時 pipeline 繼續跑完。

        CARD-04 更新：原本測試的是 classify 失敗仍繼續，但 classify 已升為
        CRITICAL_STEPS，失敗應中止。改為測試 tw_highlight（非關鍵）失敗後
        pipeline 繼續執行並以 formatter 決定的 status 結束。
        """
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        mocks = {k: p.start() for k, p in patches.items()}
        # tw_highlight 非關鍵步驟失敗，pipeline 應繼續
        mocks["src.pipeline.tw_highlight"].return_value = 1

        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": [], "dropped": []}
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))

        with patch("src.pipeline.generate_all_outputs") as mock_fmt:
            mock_fmt.return_value = ({"status": "partial"}, [])
            summary = run_pipeline("2026-05-20", dry_run=True, output_base=tmp_path / "out")

        assert summary["status"] == "partial"
        assert len(summary["steps"]) == 9
        # tw_highlight 步驟有跑且 exit_code == 1
        tw_step = next(s for s in summary["steps"] if s["name"] == "tw_highlight")
        assert tw_step["exit_code"] == 1

        for p in patches.values():
            p.stop()

    def test_beat_counts_computed(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        for p in patches.values():
            p.start()

        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": ["e1", "e2"], "dropped": []}
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))
        (evt_dir / "e1.json").write_text(json.dumps({"event_id": "e1", "beat": "INTL"}))
        (evt_dir / "e2.json").write_text(json.dumps({"event_id": "e2", "beat": "INTL"}))

        with patch("src.pipeline.generate_all_outputs") as mock_fmt:
            mock_fmt.return_value = ({"status": "ok"}, [])
            summary = run_pipeline("2026-05-20", dry_run=True, output_base=tmp_path / "out")

        assert summary["events_count"] == 2
        assert summary["beat_counts"] == {"INTL": 2}

        for p in patches.values():
            p.stop()

    def test_formatter_exception_handled(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        for p in patches.values():
            p.start()

        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": [], "dropped": []}
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))

        with patch("src.pipeline.generate_all_outputs") as mock_fmt:
            mock_fmt.side_effect = RuntimeError("format error")
            summary = run_pipeline("2026-05-20", dry_run=True, output_base=tmp_path / "out")

        assert summary["status"] == "failed"
        fmt_step = summary["steps"][-1]
        assert fmt_step["name"] == "formatter"
        assert fmt_step["exit_code"] == 99

        for p in patches.values():
            p.stop()

    def test_idempotent_rerun_same_output(self, tmp_path, monkeypatch):
        """Running pipeline twice for the same date produces identical summary."""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        for p in patches.values():
            p.start()

        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {
            "selected_event_ids": ["e1", "e2"],
            "dropped": [{"event_id": "e3", "drop_reason": "low_score"}],
        }
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))
        (evt_dir / "e1.json").write_text(json.dumps({"event_id": "e1", "beat": "INTL"}))
        (evt_dir / "e2.json").write_text(json.dumps({"event_id": "e2", "beat": "AI"}))

        out_dir = tmp_path / "output"

        def _run_once():
            with patch("src.pipeline.generate_all_outputs") as mock_fmt:
                mock_fmt.return_value = (
                    {"status": "ok", "reportId": "daily-report-2026-05-20"},
                    [],
                )
                return run_pipeline("2026-05-20", dry_run=True, output_base=out_dir)

        s1 = _run_once()
        s2 = _run_once()

        assert s1["status"] == s2["status"] == "ok"
        assert s1["events_count"] == s2["events_count"] == 2
        assert s1["beat_counts"] == s2["beat_counts"]
        assert len(s1["steps"]) == len(s2["steps"]) == 9
        for a, b in zip(s1["steps"], s2["steps"]):
            assert a["name"] == b["name"]
            assert a["exit_code"] == b["exit_code"]

        for p in patches.values():
            p.stop()

    def test_idempotent_output_files_overwritten(self, tmp_path, monkeypatch):
        """Re-running overwrites output files rather than creating duplicates."""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        for p in patches.values():
            p.start()

        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": [], "dropped": []}
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))

        out_dir = tmp_path / "output"
        sentinel = out_dir / "daily_20260520.json"

        for run_num in range(1, 3):
            with patch("src.pipeline.generate_all_outputs") as mock_fmt:
                def _write_output(*a, **kw):
                    sentinel.parent.mkdir(parents=True, exist_ok=True)
                    sentinel.write_text(json.dumps({"run": run_num}))
                    return {"status": "ok"}, []
                mock_fmt.side_effect = _write_output
                run_pipeline("2026-05-20", dry_run=True, output_base=out_dir)

        # File should exist with second run's content (overwritten, not duplicated)
        assert sentinel.exists()
        data = json.loads(sentinel.read_text())
        assert data["run"] == 2
        # No duplicate files
        json_files = list(out_dir.glob("daily_20260520*.json"))
        assert len(json_files) == 1

        for p in patches.values():
            p.stop()

    # ------------------------------------------------------------------
    # CARD-04：關鍵步驟中止 / 非關鍵步驟降級
    # ------------------------------------------------------------------

    def test_classify_critical_abort(self, tmp_path, monkeypatch):
        """classify 回傳 1 → summary status==failed、reason 含 critical_step_failed:classify，exit 2。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        mocks = {k: p.start() for k, p in patches.items()}
        mocks["src.pipeline.classifier"].return_value = 1

        summary = run_pipeline("2026-05-20", dry_run=True)

        assert summary["status"] == "failed"
        assert summary["reason"] == "critical_step_failed:classify"
        # pipeline 在 classify 後中止，後續步驟不應執行
        step_names = [s["name"] for s in summary["steps"]]
        assert "classify" in step_names
        assert "tw_highlight" not in step_names
        # formatter 不執行
        assert "formatter" not in step_names

        # main() 應回傳 exit code 2
        from src.pipeline import main as pipeline_main
        with patch("src.pipeline.run_pipeline", return_value=summary):
            rc = pipeline_main(["--date", "2026-05-20"])
        assert rc == 2

        for p in patches.values():
            p.stop()

    def test_tw_highlight_noncritical_warning(self, tmp_path, monkeypatch):
        """tw_highlight 回傳 1 → pipeline 跑完、status partial、warnings 含 step 訊息。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        mocks = {k: p.start() for k, p in patches.items()}
        mocks["src.pipeline.tw_highlight"].return_value = 1

        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": [], "dropped": []}
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))

        captured_warnings: list[list] = []

        def _fake_generate(*, pipeline_warnings, **kw):
            captured_warnings.append(list(pipeline_warnings))
            # formatter 見到非空 warnings → partial
            return ({"status": "partial"}, [])

        with patch("src.pipeline.generate_all_outputs", side_effect=_fake_generate):
            summary = run_pipeline("2026-05-20", dry_run=True, output_base=tmp_path / "out")

        # pipeline 跑完（含 formatter）
        assert summary["status"] == "partial"
        assert len(summary["steps"]) == 9

        # warnings 傳入 generate_all_outputs
        assert len(captured_warnings) == 1
        warnings_passed = captured_warnings[0]
        assert any(
            w.get("type") == "other" and "tw_highlight" in w.get("message", "")
            for w in warnings_passed
        ), f"Expected tw_highlight warning, got: {warnings_passed}"

        for p in patches.values():
            p.stop()

    def test_all_green_status_unaffected(self, tmp_path, monkeypatch):
        """全步驟成功時 status 不受關鍵步驟邏輯影響，仍回傳 ok。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        for p in patches.values():
            p.start()

        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": [], "dropped": []}
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))

        with patch("src.pipeline.generate_all_outputs") as mock_fmt:
            mock_fmt.return_value = ({"status": "ok"}, [])
            summary = run_pipeline("2026-05-20", dry_run=True, output_base=tmp_path / "out")

        assert summary["status"] == "ok"
        assert "reason" not in summary
        assert len(summary["steps"]) == 9
        assert all(s["exit_code"] == 0 for s in summary["steps"])

        for p in patches.values():
            p.stop()

    def test_duration_tracked(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        for p in patches.values():
            p.start()

        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": [], "dropped": []}
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))

        with patch("src.pipeline.generate_all_outputs") as mock_fmt:
            mock_fmt.return_value = ({"status": "ok"}, [])
            summary = run_pipeline("2026-05-20", dry_run=True, output_base=tmp_path / "out")

        assert summary["total_duration_s"] >= 0
        for step in summary["steps"]:
            assert "duration_s" in step
            assert step["duration_s"] >= 0

        for p in patches.values():
            p.stop()


# ---------------------------------------------------------------------------
# CARD-15：skip-fetch 部分資料防護
# ---------------------------------------------------------------------------

def _build_feeds_yaml(enabled_count: int, remote_blocked_count: int) -> str:
    """產生最簡 feeds.yaml 字串：enabled_count 個來源，其中 remote_blocked_count 個設 remote_blocked。"""
    lines = ["sources:"]
    for i in range(enabled_count):
        rb = i < remote_blocked_count
        lines.append(f"  - source_id: src_{i:03d}")
        lines.append(f"    enabled: true")
        if rb:
            lines.append(f"    remote_blocked: true")
    return "\n".join(lines) + "\n"


class TestSkipFetchPartialData:
    """CARD-15：skip-fetch 分支的部分資料防護測試。"""

    @staticmethod
    def _mock_all_modules():
        patches = {}
        for mod_name in [
            "src.pipeline.fetch_rss",
            "src.pipeline.normalize",
            "src.pipeline.classifier",
            "src.pipeline.tw_highlight",
            "src.pipeline.dedup",
            "src.pipeline.event_cluster",
            "src.pipeline.selector",
            "src.pipeline.claude_rewrite",
        ]:
            p = patch(f"{mod_name}.main", return_value=0)
            patches[mod_name] = p
        return patches

    def _setup_env(self, tmp_path, enabled: int, remote_blocked: int, xml_files: int) -> Path:
        """建立 tmp feeds.yaml 與指定數量的 XML 假檔，回傳 raw_dir。"""
        # feeds.yaml
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "feeds.yaml").write_text(
            _build_feeds_yaml(enabled, remote_blocked), encoding="utf-8"
        )

        # raw XML 檔
        raw_dir = tmp_path / "data" / "raw" / "2026-05-20"
        raw_dir.mkdir(parents=True, exist_ok=True)
        for i in range(xml_files):
            (raw_dir / f"src_{i:03d}.xml").write_text("<rss/>", encoding="utf-8")

        # events manifest（formatter 所需）
        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True, exist_ok=True)
        (evt_dir / "_selection_manifest.json").write_text(
            json.dumps({"selected_event_ids": [], "dropped": []})
        )
        return raw_dir

    def test_partial_xml_emits_warning(self, tmp_path, monkeypatch):
        """(a) 27 enabled、0 remote_blocked、放 3 個 XML → partial 警告出現在 pipeline_warnings。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        self._setup_env(tmp_path, enabled=27, remote_blocked=0, xml_files=3)

        patches = self._mock_all_modules()
        {k: p.start() for k, p in patches.items()}

        captured_warnings: list[list] = []

        def _fake_generate(*, pipeline_warnings, **kw):
            captured_warnings.append(list(pipeline_warnings))
            return ({"status": "partial" if pipeline_warnings else "ok"}, [])

        with patch("src.pipeline.generate_all_outputs", side_effect=_fake_generate):
            summary = run_pipeline(
                "2026-05-20",
                dry_run=True,
                skip_fetch=True,
                output_base=tmp_path / "out",
            )

        for p in patches.values():
            p.stop()

        assert len(captured_warnings) == 1
        warnings_passed = captured_warnings[0]
        partial_warns = [
            w for w in warnings_passed
            if w.get("type") == "other" and "partial raw data" in w.get("message", "")
        ]
        assert len(partial_warns) == 1, f"partial 警告應出現一筆，實際 warnings: {warnings_passed}"
        msg = partial_warns[0]["message"]
        # 訊息應包含 xml_count/enabled 與 expected_min
        assert "3/27" in msg, f"訊息應含 3/27，實際：{msg}"
        assert "expected >= 27" in msg, f"訊息應含 expected >= 27，實際：{msg}"

    def test_full_xml_no_warning(self, tmp_path, monkeypatch):
        """(b) 27 enabled、0 remote_blocked、放滿 27 個 XML → 無 partial 警告。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        self._setup_env(tmp_path, enabled=27, remote_blocked=0, xml_files=27)

        patches = self._mock_all_modules()
        {k: p.start() for k, p in patches.items()}

        captured_warnings: list[list] = []

        def _fake_generate(*, pipeline_warnings, **kw):
            captured_warnings.append(list(pipeline_warnings))
            return ({"status": "ok"}, [])

        with patch("src.pipeline.generate_all_outputs", side_effect=_fake_generate):
            run_pipeline(
                "2026-05-20",
                dry_run=True,
                skip_fetch=True,
                output_base=tmp_path / "out",
            )

        for p in patches.values():
            p.stop()

        assert len(captured_warnings) == 1
        partial_warns = [
            w for w in captured_warnings[0]
            if w.get("type") == "other" and "partial raw data" in w.get("message", "")
        ]
        assert partial_warns == [], f"不應有 partial 警告，實際 warnings: {captured_warnings[0]}"

    def test_partial_xml_with_remote_blocked(self, tmp_path, monkeypatch):
        """(a 變體) 27 enabled、1 remote_blocked（expected_min=26）、放 3 個 XML → 警告含正確 expected。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        self._setup_env(tmp_path, enabled=27, remote_blocked=1, xml_files=3)

        patches = self._mock_all_modules()
        {k: p.start() for k, p in patches.items()}

        captured_warnings: list[list] = []

        def _fake_generate(*, pipeline_warnings, **kw):
            captured_warnings.append(list(pipeline_warnings))
            return ({"status": "partial" if pipeline_warnings else "ok"}, [])

        with patch("src.pipeline.generate_all_outputs", side_effect=_fake_generate):
            run_pipeline(
                "2026-05-20",
                dry_run=True,
                skip_fetch=True,
                output_base=tmp_path / "out",
            )

        for p in patches.values():
            p.stop()

        assert len(captured_warnings) == 1
        partial_warns = [
            w for w in captured_warnings[0]
            if "partial raw data" in w.get("message", "")
        ]
        assert len(partial_warns) == 1
        msg = partial_warns[0]["message"]
        assert "3/27" in msg
        assert "expected >= 26" in msg, f"訊息應含 expected >= 26，實際：{msg}"

    def test_exact_threshold_no_warning(self, tmp_path, monkeypatch):
        """(b 變體) 27 enabled、1 remote_blocked（expected_min=26）、放 26 個 → 剛好滿，無警告。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        self._setup_env(tmp_path, enabled=27, remote_blocked=1, xml_files=26)

        patches = self._mock_all_modules()
        {k: p.start() for k, p in patches.items()}

        captured_warnings: list[list] = []

        def _fake_generate(*, pipeline_warnings, **kw):
            captured_warnings.append(list(pipeline_warnings))
            return ({"status": "ok"}, [])

        with patch("src.pipeline.generate_all_outputs", side_effect=_fake_generate):
            run_pipeline(
                "2026-05-20",
                dry_run=True,
                skip_fetch=True,
                output_base=tmp_path / "out",
            )

        for p in patches.values():
            p.stop()

        assert len(captured_warnings) == 1
        partial_warns = [
            w for w in captured_warnings[0]
            if "partial raw data" in w.get("message", "")
        ]
        assert partial_warns == [], f"剛好滿不應有警告，實際: {captured_warnings[0]}"


class TestLoadFeedsCounts:
    """_load_feeds_counts 單元測試。"""

    def test_no_feeds_yaml(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        enabled, blocked = _load_feeds_counts()
        assert enabled == 0
        assert blocked == 0

    def test_counts_enabled_and_remote_blocked(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "feeds.yaml").write_text(
            _build_feeds_yaml(enabled_count=10, remote_blocked_count=3), encoding="utf-8"
        )
        enabled, blocked = _load_feeds_counts()
        assert enabled == 10
        assert blocked == 3

    def test_disabled_source_excluded(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True)
        yaml_content = (
            "sources:\n"
            "  - source_id: a\n"
            "    enabled: true\n"
            "  - source_id: b\n"
            "    enabled: false\n"
            "  - source_id: c\n"
            "    enabled: true\n"
            "    remote_blocked: true\n"
        )
        (config_dir / "feeds.yaml").write_text(yaml_content, encoding="utf-8")
        enabled, blocked = _load_feeds_counts()
        assert enabled == 2   # b は disabled なので除外
        assert blocked == 1


# ---------------------------------------------------------------------------
# CARD-16：--until 旗標
# ---------------------------------------------------------------------------

class TestUntilFlag:
    """CARD-16：run_pipeline until 參數與 main() --until 旗標。"""

    @staticmethod
    def _mock_all_modules():
        """Patch all pipeline module main() functions to return 0."""
        patches = {}
        for mod_name in [
            "src.pipeline.fetch_rss",
            "src.pipeline.normalize",
            "src.pipeline.classifier",
            "src.pipeline.tw_highlight",
            "src.pipeline.dedup",
            "src.pipeline.event_cluster",
            "src.pipeline.selector",
            "src.pipeline.claude_rewrite",
        ]:
            p = patch(f"{mod_name}.main", return_value=0)
            patches[mod_name] = p
        return patches

    def test_until_select_stops_at_select(self, tmp_path, monkeypatch):
        """(a) until="select" → 7 步紀錄、無 formatter、exit 0、summary 含 stopped_after。

        STEPS 前 7 項為 fetch_rss, normalize, classify, tw_highlight,
        dedup, event_cluster, select。
        """
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        mocks = {k: p.start() for k, p in patches.items()}

        with patch("src.pipeline.generate_all_outputs") as mock_fmt:
            summary = run_pipeline(
                "2026-05-20",
                dry_run=True,
                output_base=tmp_path / "out",
                until="select",
            )

        # formatter 不應被呼叫
        mock_fmt.assert_not_called()

        # 剛好 7 步（fetch_rss 到 select）
        assert len(summary["steps"]) == 7
        step_names = [s["name"] for s in summary["steps"]]
        assert step_names == [
            "fetch_rss", "normalize", "classify", "tw_highlight",
            "dedup", "event_cluster", "select",
        ], f"步驟清單不符：{step_names}"

        # 無 formatter 步驟
        assert "formatter" not in step_names

        # status == "ok"
        assert summary["status"] == "ok"

        # summary 含 stopped_after
        assert summary.get("stopped_after") == "select"

        # claude_rewrite 不應被呼叫
        mocks["src.pipeline.claude_rewrite"].assert_not_called()

        for p in patches.values():
            p.stop()

    def test_until_select_writes_run_state_for_formatter(self, tmp_path, monkeypatch):
        """FIX-C (0706 健檢): --until select 提前停止時，須把 step_records 與
        pipeline_start 落地到 _pipeline_run_state.json，讓稍後單獨執行的
        formatter 能接續產生忠實的 run log（steps 非空、duration 涵蓋全程）。
        """
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        {k: p.start() for k, p in patches.items()}

        with patch("src.pipeline.generate_all_outputs"):
            summary = run_pipeline(
                "2026-05-20",
                dry_run=True,
                output_base=tmp_path / "out",
                until="select",
            )

        state_path = tmp_path / "data" / "events" / "2026-05-20" / "_pipeline_run_state.json"
        assert state_path.exists()
        state = json.loads(state_path.read_text(encoding="utf-8"))

        # 7 步（fetch_rss ~ select）都落地
        assert len(state["steps"]) == 7
        assert [s["name"] for s in state["steps"]] == [
            "fetch_rss", "normalize", "classify", "tw_highlight",
            "dedup", "event_cluster", "select",
        ]
        # pipeline_start 應是個合理的 epoch 時間（早於現在）
        assert state["pipeline_start"] <= time.time()

        # read_pipeline_run_state 能讀回同樣的內容
        read_back = read_pipeline_run_state("2026-05-20")
        assert read_back == state

        for p in patches.values():
            p.stop()

    def test_read_pipeline_run_state_missing_file_returns_none(self, tmp_path, monkeypatch):
        """FIX-C: 沒有 run state 檔（例如一次跑完全程沒分段）→ 回傳 None。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)
        assert read_pipeline_run_state("2026-01-01") is None

    def test_until_select_main_exits_0(self, tmp_path, monkeypatch):
        """(a) --until select → main() 回傳 0（exit 0）。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        {k: p.start() for k, p in patches.items()}

        from src.pipeline import main as pipeline_main

        with patch("src.pipeline.generate_all_outputs"):
            rc = pipeline_main(["--date", "2026-05-20", "--until", "select"])

        assert rc == 0

        for p in patches.values():
            p.stop()

    def test_until_none_full_pipeline(self, tmp_path, monkeypatch):
        """(b) 不給 until → 全 9 步正常跑完，既有行為零變動。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        for p in patches.values():
            p.start()

        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": [], "dropped": []}
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))

        with patch("src.pipeline.generate_all_outputs") as mock_fmt:
            mock_fmt.return_value = ({"status": "ok"}, [])
            summary = run_pipeline(
                "2026-05-20",
                dry_run=True,
                output_base=tmp_path / "out",
                until=None,
            )

        # formatter 有被呼叫
        mock_fmt.assert_called_once()

        # 全 9 步
        assert len(summary["steps"]) == 9
        assert summary["steps"][-1]["name"] == "formatter"

        # 無 stopped_after
        assert "stopped_after" not in summary

        assert summary["status"] == "ok"

        for p in patches.values():
            p.stop()

    def test_until_formatter_equals_no_until(self, tmp_path, monkeypatch):
        """--until formatter 等同不給，formatter 照常執行，9 步。"""
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        for p in patches.values():
            p.start()

        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": [], "dropped": []}
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))

        with patch("src.pipeline.generate_all_outputs") as mock_fmt:
            mock_fmt.return_value = ({"status": "ok"}, [])
            summary = run_pipeline(
                "2026-05-20",
                dry_run=True,
                output_base=tmp_path / "out",
                until="formatter",
            )

        mock_fmt.assert_called_once()
        assert len(summary["steps"]) == 9
        assert "stopped_after" not in summary

        for p in patches.values():
            p.stop()

    def test_until_invalid_value_raises(self, tmp_path, monkeypatch):
        """(c) --until BOGUS_STEP → argparse choices 約束觸發 SystemExit(2)。

        非法值（非 STEPS 內名稱）應讓 main() 以非 0 退出，不可靜默接受或跑完 pipeline。
        """
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        from src.pipeline import main as pipeline_main

        with pytest.raises(SystemExit) as exc_info:
            pipeline_main(["--date", "2026-05-20", "--until", "BOGUS_STEP", "--dry-run"])

        # argparse choices 驗證失敗固定回傳 exit code 2
        assert exc_info.value.code == 2
