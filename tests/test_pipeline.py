"""Tests for src/pipeline.py — pipeline orchestrator."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline import (
    _collect_stats,
    _read_selected_events,
    _run_module_step,
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
        monkeypatch.setattr("src.pipeline.PROJECT_ROOT", tmp_path)

        patches = self._mock_all_modules()
        mocks = {k: p.start() for k, p in patches.items()}
        # classify fails but pipeline continues
        mocks["src.pipeline.classifier"].return_value = 1

        evt_dir = tmp_path / "data" / "events" / "2026-05-20"
        evt_dir.mkdir(parents=True)
        manifest = {"selected_event_ids": [], "dropped": []}
        (evt_dir / "_selection_manifest.json").write_text(json.dumps(manifest))

        with patch("src.pipeline.generate_all_outputs") as mock_fmt:
            mock_fmt.return_value = ({"status": "partial"}, [])
            summary = run_pipeline("2026-05-20", dry_run=True, output_base=tmp_path / "out")

        assert summary["status"] == "partial"
        assert len(summary["steps"]) == 9
        # All steps ran despite classify failure
        assert summary["steps"][2]["name"] == "classify"
        assert summary["steps"][2]["exit_code"] == 1

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
