"""Phase 5 — Full pipeline orchestrator.

Runs all Phase 1–4 modules in sequence to produce the daily report.
Each step reads from and writes to the filesystem under data/ and output/.

Data flow:
    fetch_rss    → data/raw/{date}/
    normalize    → data/articles/{date}/
    classify     → enriches data/articles/{date}/ in-place
    tw_highlight → enriches data/articles/{date}/ in-place
    dedup        → removes duplicates from data/articles/{date}/
    event_cluster→ data/events/{date}/
    selector     → data/events/{date}/_selection_manifest.json
    claude_rewrite → enriches data/events/{date}/ in-place
    formatter    → output/daily_YYYYMMDD.{json,md} etc.

CLI:
    python -m src.pipeline                     # Today (Asia/Taipei)
    python -m src.pipeline --date 2026-05-20   # Specific date
    python -m src.pipeline --dry-run           # Skip Claude API + file writing

Exit codes:
    0   Success
    2   Fatal — all sources failed or critical step failed
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from src import (
    fetch_rss,
    normalize,
    classifier,
    tw_highlight,
    dedup,
    event_cluster,
    selector,
    claude_rewrite,
)
from src.formatter import generate_all_outputs, OUTPUT_BASE

LOG = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TAIPEI = timezone(timedelta(hours=8))

STEPS = [
    "fetch_rss",
    "normalize",
    "classify",
    "tw_highlight",
    "dedup",
    "event_cluster",
    "select",
    "claude_rewrite",
    "formatter",
]

MODULE_MAP = {
    "fetch_rss": fetch_rss,
    "normalize": normalize,
    "classify": classifier,
    "tw_highlight": tw_highlight,
    "dedup": dedup,
    "event_cluster": event_cluster,
    "select": selector,
    "claude_rewrite": claude_rewrite,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_module_step(name: str, module, date: str, dry_run: bool) -> tuple[int, float]:
    """Call a module's main(argv) and return (exit_code, duration_seconds)."""
    argv = ["--date", date]
    if dry_run and name == "claude_rewrite":
        argv.append("--dry-run")

    start = time.time()
    try:
        rc = module.main(argv)
    except SystemExit as exc:
        rc = exc.code if isinstance(exc.code, int) else 1
    except Exception:
        LOG.exception("Step %s raised an exception", name)
        rc = 99
    return rc, time.time() - start


def _collect_stats(date: str) -> dict:
    """Read filesystem state after all steps to build accurate pipeline_stats."""
    raw_dir = PROJECT_ROOT / "data" / "raw" / date
    articles_dir = PROJECT_ROOT / "data" / "articles" / date
    events_dir = PROJECT_ROOT / "data" / "events" / date

    stats: dict = {
        "total_feeds_checked": 0,
        "total_feeds_failed": 0,
        "total_articles_fetched": 0,
        "total_articles_after_filter": 0,
        "total_events_merged": 0,
        "total_events_selected": 0,
        "tw_highlights_count": 0,
    }

    health_path = raw_dir / "feed_health.json"
    if health_path.exists():
        health = json.loads(health_path.read_text(encoding="utf-8"))
        stats["total_feeds_checked"] = len(health)
        stats["total_feeds_failed"] = sum(
            1 for h in health if h.get("status") != "ok"
        )
        stats["total_articles_fetched"] = sum(
            h.get("items_valid", 0) for h in health
        )

    if articles_dir.exists():
        article_files = [
            f for f in articles_dir.glob("*.json") if not f.name.startswith("_")
        ]
        stats["total_articles_after_filter"] = len(article_files)

    manifest_path = events_dir / "_selection_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        selected_ids = manifest.get("selected_event_ids", [])
        dropped = manifest.get("dropped", [])
        stats["total_events_merged"] = len(selected_ids) + len(dropped)
        stats["total_events_selected"] = len(selected_ids)

    return stats


def _read_selected_events(date: str) -> tuple[list[dict], list[dict], list[dict]]:
    """Read selected events, dropped list, and rewrite warnings from disk."""
    events_dir = PROJECT_ROOT / "data" / "events" / date
    manifest_path = events_dir / "_selection_manifest.json"

    if not manifest_path.exists():
        return [], [], []

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected_ids = set(manifest.get("selected_event_ids", []))
    dropped = manifest.get("dropped", [])

    events = []
    for eid in selected_ids:
        fp = events_dir / f"{eid}.json"
        if fp.exists():
            events.append(json.loads(fp.read_text(encoding="utf-8")))
        else:
            LOG.warning("Event file not found: %s", fp)

    rewrite_log_path = events_dir / "_rewrite_log.json"
    rewrite_warnings: list[dict] = []
    if rewrite_log_path.exists():
        rlog = json.loads(rewrite_log_path.read_text(encoding="utf-8"))
        rewrite_warnings = rlog.get("lint_warnings", [])

    return events, dropped, rewrite_warnings


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def run_pipeline(
    date: str,
    dry_run: bool = False,
    skip_fetch: bool = False,
    output_base: Optional[Path] = None,
) -> dict:
    """Run the full daily pipeline and return a summary dict.

    Args:
        skip_fetch: If True, skip fetch_rss step (use pre-fetched raw data).
                    Useful when raw data is pushed by a local fetch job.
    """
    pipeline_start = time.time()
    _output_base = output_base or OUTPUT_BASE
    step_records: list[dict] = []

    # ------------------------------------------------------------------
    # Steps 1–8: call each module's main(argv)
    # ------------------------------------------------------------------
    for name in STEPS[:-1]:  # all except formatter
        # Skip fetch if raw data already exists
        if name == "fetch_rss" and skip_fetch:
            raw_dir = PROJECT_ROOT / "data" / "raw" / date
            if raw_dir.exists() and any(raw_dir.glob("*.xml")):
                xml_count = len(list(raw_dir.glob("*.xml")))
                LOG.info("SKIP fetch_rss: %d raw XML files found in %s", xml_count, raw_dir)
                step_records.append({
                    "name": "fetch_rss",
                    "exit_code": 0,
                    "duration_s": 0.0,
                    "skipped": True,
                    "note": f"pre-fetched ({xml_count} XML files)",
                })
                continue
            else:
                LOG.warning("--skip-fetch but no raw data at %s; running fetch anyway", raw_dir)

        module = MODULE_MAP[name]
        LOG.info("=" * 60)
        LOG.info("PIPELINE STEP: %s", name)
        LOG.info("=" * 60)

        rc, duration = _run_module_step(name, module, date, dry_run)
        step_records.append({
            "name": name,
            "exit_code": rc,
            "duration_s": round(duration, 2),
        })
        LOG.info("Step %s → exit %d (%.1fs)", name, rc, duration)

        if name == "fetch_rss" and rc == 2:
            LOG.error("ABORT: all sources failed — stopping pipeline")
            return {
                "status": "failed",
                "date": date,
                "reason": "all_sources_failed",
                "steps": step_records,
                "events_count": 0,
                "beat_counts": {},
                "validation_issues": 0,
                "total_duration_s": round(time.time() - pipeline_start, 2),
            }

    # ------------------------------------------------------------------
    # Step 9: formatter — call generate_all_outputs with real stats
    # ------------------------------------------------------------------
    LOG.info("=" * 60)
    LOG.info("PIPELINE STEP: formatter")
    LOG.info("=" * 60)

    format_start = time.time()
    stats = _collect_stats(date)
    events, dropped, rewrite_warnings = _read_selected_events(date)
    stats["tw_highlights_count"] = sum(1 for e in events if e.get("tw_highlight"))

    try:
        report, validation_issues = generate_all_outputs(
            date_str=date,
            rewritten_events=events,
            dropped_events=dropped,
            pipeline_warnings=rewrite_warnings,
            pipeline_stats=stats,
            steps=step_records,
            start_time=pipeline_start,
            output_base=Path(_output_base),
            dry_run=dry_run,
        )
        fmt_rc = 0
    except Exception:
        LOG.exception("Formatter raised an exception")
        report, validation_issues = {}, []
        fmt_rc = 99

    step_records.append({
        "name": "formatter",
        "exit_code": fmt_rc,
        "duration_s": round(time.time() - format_start, 2),
    })

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    beat_counts: dict[str, int] = {}
    for e in events:
        b = e.get("beat", "?")
        beat_counts[b] = beat_counts.get(b, 0) + 1

    return {
        "status": report.get("status", "failed"),
        "date": date,
        "steps": step_records,
        "events_count": len(events),
        "beat_counts": beat_counts,
        "validation_issues": len(validation_issues),
        "total_duration_s": round(time.time() - pipeline_start, 2),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_summary(summary: dict) -> None:
    status = summary["status"]
    date = summary["date"]
    ok = status != "failed"

    print()
    print(f"  akasha-rss-news | {date} | {'DONE' if ok else 'FAILED'}")
    print(f"  status: {status}")
    print(f"  events: {summary.get('events_count', 0)}")
    for beat, n in sorted(summary.get("beat_counts", {}).items()):
        print(f"    {beat}: {n}")
    if summary.get("validation_issues"):
        print(f"  validation issues: {summary['validation_issues']}")
    print(f"  duration: {summary['total_duration_s']:.1f}s")
    print()
    for step in summary.get("steps", []):
        icon = "ok" if step["exit_code"] == 0 else "WARN"
        print(f"    [{icon:>4}] {step['name']:<16} exit={step['exit_code']}  {step['duration_s']:.1f}s")
    print()
    if ok:
        dc = date.replace("-", "")
        print(f"  output/daily_{dc}.json")
        print(f"  output/daily_{dc}.md")
        print(f"  output/voice_{dc}.txt")
        print(f"  output/platforms/x_{dc}.json")
        print(f"  output/platforms/threads_{dc}.json")
        print(f"  output/logs/run_{dc}.json")
    print()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run full daily report pipeline (fetch -> format).",
    )
    parser.add_argument(
        "--date", type=str, default=None,
        help="Report date YYYY-MM-DD (default: today Asia/Taipei)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Skip Claude API calls and file writing",
    )
    parser.add_argument(
        "--skip-fetch", action="store_true",
        help="Skip fetch_rss step; use pre-fetched raw data from data/raw/{date}/",
    )
    parser.add_argument(
        "--output-base", type=Path, default=None,
        help="Override output directory",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    date = args.date or datetime.now(TAIPEI).strftime("%Y-%m-%d")
    flags = []
    if args.dry_run:
        flags.append("dry-run")
    if args.skip_fetch:
        flags.append("skip-fetch")
    LOG.info("Pipeline start: %s%s", date, f" ({', '.join(flags)})" if flags else "")

    summary = run_pipeline(date, args.dry_run, args.skip_fetch, args.output_base)
    _print_summary(summary)

    if summary["status"] == "failed":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
