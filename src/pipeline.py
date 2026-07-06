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

import yaml

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

# 關鍵步驟：rc != 0 時立即中止整條 pipeline
CRITICAL_STEPS: frozenset[str] = frozenset({"normalize", "classify"})

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


def _load_remote_blocked_ids() -> set[str]:
    """Load source_ids marked remote_blocked in feeds.yaml."""
    feeds_path = PROJECT_ROOT / "config" / "feeds.yaml"
    if not feeds_path.exists():
        return set()
    try:
        cfg = yaml.safe_load(feeds_path.read_text(encoding="utf-8"))
        return {
            s["source_id"]
            for s in cfg.get("sources", [])
            if s.get("remote_blocked")
        }
    except Exception:
        LOG.warning("Could not load feeds.yaml for remote_blocked check")
        return set()


def _load_feeds_counts() -> tuple[int, int]:
    """從 feeds.yaml 讀取 enabled 來源數與 remote_blocked enabled 來源數。

    Returns:
        (enabled_count, remote_blocked_count) 兩者皆為 enabled:true 的子集。
        若讀取失敗，回傳 (0, 0)（呼叫端應容忍此情況）。
    """
    feeds_path = PROJECT_ROOT / "config" / "feeds.yaml"
    if not feeds_path.exists():
        return 0, 0
    try:
        cfg = yaml.safe_load(feeds_path.read_text(encoding="utf-8"))
        sources = cfg.get("sources", [])
        enabled = [s for s in sources if s.get("enabled", True)]
        remote_blocked = [s for s in enabled if s.get("remote_blocked")]
        return len(enabled), len(remote_blocked)
    except Exception:
        LOG.warning("無法讀取 feeds.yaml 以計算來源數")
        return 0, 0


def _collect_stats(date: str) -> dict:
    """Read filesystem state after all steps to build accurate pipeline_stats."""
    raw_dir = PROJECT_ROOT / "data" / "raw" / date
    articles_dir = PROJECT_ROOT / "data" / "articles" / date
    events_dir = PROJECT_ROOT / "data" / "events" / date

    stats: dict = {
        "total_feeds_checked": 0,
        "total_feeds_failed": 0,
        "total_feeds_failed_remote_blocked": 0,
        "total_articles_fetched": 0,
        "total_articles_after_filter": 0,
        "total_events_merged": 0,
        "total_events_selected": 0,
        "tw_highlights_count": 0,
    }

    health_path = raw_dir / "feed_health.json"
    if health_path.exists():
        health = json.loads(health_path.read_text(encoding="utf-8"))
        remote_blocked = _load_remote_blocked_ids()
        failed = [h for h in health if h.get("status") != "ok"]
        stats["total_feeds_checked"] = len(health)
        stats["total_feeds_failed"] = len(failed)
        stats["total_feeds_failed_remote_blocked"] = sum(
            1 for h in failed if h.get("source_id") in remote_blocked
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


def _read_fetch_warnings(date: str) -> list[dict]:
    """讀取 data/raw/{date}/fetch_warnings.json，過濾 remote_blocked 來源後回傳剩餘 warnings。

    規格 CARD-06：
    - 檔案不存在回傳空 list。
    - 過濾掉 source_id 屬於 feeds.yaml 中 remote_blocked: true 的條目（沿用 _load_remote_blocked_ids）。
    - 警告 type 沿用 "source_failed"，以便 _format_warnings 正確處理。
    """
    warnings_path = PROJECT_ROOT / "data" / "raw" / date / "fetch_warnings.json"
    if not warnings_path.exists():
        return []
    try:
        raw = json.loads(warnings_path.read_text(encoding="utf-8"))
    except Exception:
        LOG.warning("無法讀取 fetch_warnings.json: %s", warnings_path)
        return []

    blocked_ids = _load_remote_blocked_ids()
    result: list[dict] = []
    for w in raw:
        sid = w.get("source_id", "")
        if sid in blocked_ids:
            LOG.debug("過濾 remote_blocked fetch warning: %s", sid)
            continue
        # 確保 type 為 source_failed
        entry = dict(w)
        if entry.get("type") not in ("source_failed",):
            entry["type"] = "source_failed"
        result.append(entry)
    return result


def _pipeline_run_state_path(date: str) -> Path:
    """FIX-C (0706 健檢) 用：跨程序（分兩段跑）交接 run log 所需狀態的檔案路徑。"""
    return PROJECT_ROOT / "data" / "events" / date / "_pipeline_run_state.json"


def _write_pipeline_run_state(date: str, step_records: list[dict], pipeline_start: float) -> None:
    """FIX-C (0706 健檢)：Routine 分兩段跑（pipeline --until select 後，formatter 單獨跑），
    formatter 產生 run log 時原本讀不到前段步驟與真正的 pipeline 起始時間，
    導致 run log 的 steps=[]、duration 只算 formatter 自己的時間。

    在 pipeline 提前停止（--until）時，把已執行的 step_records 與
    pipeline_start 落地到 data/events/{date}/_pipeline_run_state.json，
    供之後單獨執行的 `python -m src.formatter` 讀取合併。
    """
    events_dir = PROJECT_ROOT / "data" / "events" / date
    events_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "steps": step_records,
        "pipeline_start": pipeline_start,
    }
    _pipeline_run_state_path(date).write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8",
    )


def read_pipeline_run_state(date: str) -> Optional[dict]:
    """讀取 `_write_pipeline_run_state` 寫入的狀態；不存在則回傳 None。"""
    path = _pipeline_run_state_path(date)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        LOG.warning("無法讀取 pipeline run state: %s", path)
        return None


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
    until: Optional[str] = None,
) -> dict:
    """Run the full daily pipeline and return a summary dict.

    Args:
        skip_fetch: If True, skip fetch_rss step (use pre-fetched raw data).
                    Useful when raw data is pushed by a local fetch job.
        until: 若指定，執行到該步驟（含）即停，不執行後續步驟與 formatter。
               合法值為 STEPS 內的名稱（如 "select"）。
               指定 "formatter" 或不給等同不限制。
    """
    pipeline_start = time.time()
    _output_base = output_base or OUTPUT_BASE
    step_records: list[dict] = []

    # 正規化 until：None 或 "formatter" 均視為不限制
    _until: Optional[str] = until if (until and until != "formatter") else None

    # ------------------------------------------------------------------
    # Steps 1–8: call each module's main(argv)
    # ------------------------------------------------------------------
    step_warnings: list[dict] = []  # 非關鍵步驟失敗時累積的警告

    for name in STEPS[:-1]:  # all except formatter
        # Skip fetch if raw data already exists
        if name == "fetch_rss" and skip_fetch:
            raw_dir = PROJECT_ROOT / "data" / "raw" / date
            if raw_dir.exists() and any(raw_dir.glob("*.xml")):
                xml_count = len(list(raw_dir.glob("*.xml")))
                LOG.info("SKIP fetch_rss: %d raw XML files found in %s", xml_count, raw_dir)
                # CARD-15：部分資料防護——比較 xml_count 與 enabled 來源數
                enabled_count, remote_blocked_count = _load_feeds_counts()
                expected_min = enabled_count - remote_blocked_count
                if enabled_count > 0 and xml_count < expected_min:
                    _warn_msg = (
                        f"partial raw data: {xml_count}/{enabled_count} sources"
                        f" (expected >= {expected_min})"
                    )
                    LOG.warning("skip-fetch 部分資料警告：%s", _warn_msg)
                    step_warnings.append({"type": "other", "message": _warn_msg})
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

        if name in CRITICAL_STEPS and rc != 0:
            LOG.error("ABORT: 關鍵步驟 %s 失敗（exit %d）— 停止 pipeline", name, rc)
            return {
                "status": "failed",
                "date": date,
                "reason": f"critical_step_failed:{name}",
                "steps": step_records,
                "events_count": 0,
                "beat_counts": {},
                "validation_issues": 0,
                "total_duration_s": round(time.time() - pipeline_start, 2),
            }

        if name not in CRITICAL_STEPS and name != "fetch_rss" and rc != 0:
            warn = {"type": "other", "message": f"step {name} exited {rc}"}
            step_warnings.append(warn)
            LOG.warning("非關鍵步驟 %s 失敗（exit %d），累積警告並繼續", name, rc)

        # --until 提前停止：已執行到指定步驟，跳過後續步驟與 formatter
        if _until and name == _until:
            LOG.info("--until %s：已執行完，提前停止 pipeline", _until)
            # FIX-C (0706 健檢): 落地 step_records + pipeline_start，
            # 讓稍後單獨執行的 formatter 能接續產生忠實的 run log。
            _write_pipeline_run_state(date, step_records, pipeline_start)
            return {
                "status": "ok",
                "date": date,
                "stopped_after": _until,
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
    stats["tw_highlights_count"] = sum(
        1 for e in events if e.get("tw_highlight") or e.get("beat") == "PTS_LOCAL"
    )

    # 合併非關鍵步驟警告（step_warnings）、rewrite 階段的 lint_warnings 與 fetch warnings（過濾 remote_blocked）
    fetch_warnings = _read_fetch_warnings(date)
    pipeline_warnings = step_warnings + rewrite_warnings + fetch_warnings

    try:
        report, validation_issues = generate_all_outputs(
            date_str=date,
            rewritten_events=events,
            dropped_events=dropped,
            pipeline_warnings=pipeline_warnings,
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
    stopped_after = summary.get("stopped_after")

    print()
    print(f"  akasha-rss-news | {date} | {'DONE' if ok else 'FAILED'}")
    print(f"  status: {status}")
    if stopped_after:
        print(f"  stopped_after: {stopped_after}")
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
    # 提前停止時不印輸出檔案清單（因為沒產出 formatter 結果）
    if ok and not stopped_after:
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
    parser.add_argument(
        "--until", type=str, default=None, choices=STEPS, metavar="STEP",
        help=(
            f"執行到指定步驟（含）即停，不跑後續步驟與 formatter。"
            f" 合法值：{', '.join(STEPS)}"
        ),
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
    if args.until:
        flags.append(f"until={args.until}")
    LOG.info("Pipeline start: %s%s", date, f" ({', '.join(flags)})" if flags else "")

    summary = run_pipeline(date, args.dry_run, args.skip_fetch, args.output_base, args.until)
    _print_summary(summary)

    if summary["status"] == "failed":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
