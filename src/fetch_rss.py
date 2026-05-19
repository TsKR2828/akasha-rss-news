"""Phase 1 — fetch RSS feeds and record health.

對應規格：
- §4   Feed Health 與失敗處理
- §4.1 健康檢查（timeout 10s + 2 retries + exponential backoff）
- §4.2 失敗模式（continue_with_warning / abort_report）
- §4.3 health log 欄位
- §5   資料處理流程 Step 1

CLI 用法：
    python -m src.fetch_rss                          # 預設今天 + 全部來源
    python -m src.fetch_rss --only bbc_world         # 只抓單一來源
    python -m src.fetch_rss --date 2026-05-18        # 指定報告日期

退出碼：
    0   全部成功或部分失敗（continue_with_warning）
    2   全部來源失敗（abort_report）— 不產出假成功報告
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests
import yaml

LOG = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FEEDS = PROJECT_ROOT / "config" / "feeds.yaml"
DEFAULT_OUT_BASE = PROJECT_ROOT / "data" / "raw"
STATE_FILE = PROJECT_ROOT / "data" / "feed_health_state.json"

TAIPEI = timezone(timedelta(hours=8))
USER_AGENT = "akasha-rss-news/0.1 (+https://github.com/TsKR2828/akasha-rss-news)"


@dataclass
class FetchResult:
    """規格 §4.3 health log fields."""
    source_id: str
    status: str  # "ok" | "failed"
    http_status: Optional[int] = None
    fetched_at: str = ""
    items_found: int = 0
    items_valid: int = 0  # 由 normalize 步驟回填
    error: Optional[str] = None
    consecutive_failures: int = 0


# ---------------------------------------------------------------------------
# State management — 跨次執行追蹤 consecutive_failures
# ---------------------------------------------------------------------------

def load_state() -> dict[str, int]:
    """讀取每個 source 的 consecutive_failures 計數。"""
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        LOG.warning("Failed to load state from %s: %s", STATE_FILE, e)
        return {}


def save_state(state: dict[str, int]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_feeds(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Single source fetch
# ---------------------------------------------------------------------------

def fetch_one(
    source: dict,
    timeout: int = 10,
    retries: int = 2,
    backoff_base: float = 1.0,
    session: Optional[requests.Session] = None,
) -> tuple[FetchResult, Optional[bytes]]:
    """抓取單一 source，含 exponential backoff retry。

    Returns:
        (FetchResult, raw_bytes_or_None)
    """
    sess = session or requests.Session()
    sess.headers.setdefault("User-Agent", USER_AGENT)
    last_error: Optional[Exception] = None
    last_status: Optional[int] = None
    fetched_at = datetime.now(TAIPEI).isoformat()

    for attempt in range(retries + 1):
        try:
            resp = sess.get(source["url"], timeout=timeout)
            last_status = resp.status_code
            resp.raise_for_status()
            return (
                FetchResult(
                    source_id=source["source_id"],
                    status="ok",
                    http_status=resp.status_code,
                    fetched_at=fetched_at,
                ),
                resp.content,
            )
        except requests.RequestException as e:
            last_error = e
            if attempt < retries:
                time.sleep(backoff_base * (2 ** attempt))

    return (
        FetchResult(
            source_id=source["source_id"],
            status="failed",
            http_status=last_status,
            fetched_at=fetched_at,
            error=str(last_error) if last_error else "unknown",
        ),
        None,
    )


# ---------------------------------------------------------------------------
# Concurrent fetch with state tracking
# ---------------------------------------------------------------------------

def fetch_all(
    sources: list[dict],
    timeout: int = 10,
    retries: int = 2,
    max_workers: int = 8,
) -> tuple[list[tuple[FetchResult, Optional[bytes]]], dict[str, int]]:
    """併發抓取所有 enabled sources，更新並持久化 consecutive_failures 狀態。

    Returns:
        ([(FetchResult, raw_bytes|None), ...], updated_state)
    """
    state = load_state()
    enabled = [s for s in sources if s.get("enabled", True)]

    fetched: list[tuple[FetchResult, Optional[bytes]]] = []
    with cf.ThreadPoolExecutor(max_workers=max_workers) as exe:
        futures = {exe.submit(fetch_one, s, timeout, retries): s for s in enabled}
        for fut in cf.as_completed(futures):
            result, raw = fut.result()
            sid = result.source_id
            if result.status == "ok":
                state[sid] = 0
                result.consecutive_failures = 0
            else:
                state[sid] = state.get(sid, 0) + 1
                result.consecutive_failures = state[sid]
            fetched.append((result, raw))

    save_state(state)
    return fetched, state


# ---------------------------------------------------------------------------
# Fail mode decision (規格 §4.2)
# ---------------------------------------------------------------------------

def decide_overall_status(
    results: list[FetchResult],
    enabled_sources: list[dict],
    alert_after: int = 3,
) -> tuple[str, list[dict]]:
    """根據各 source 結果決定整體 status 與 warnings。

    Returns:
        (overall_status, warnings)
        overall_status: "ok" | "partial" | "failed"
    """
    warnings: list[dict] = []
    failed_ids = {r.source_id for r in results if r.status != "ok"}
    enabled_ids = {s["source_id"] for s in enabled_sources}

    # 規格 §4.2: all_sources_failed → abort_report
    if enabled_ids and failed_ids == enabled_ids:
        warnings.append({
            "type": "other",
            "source_id": None,
            "message": "All enabled sources failed; aborting report.",
        })
        return "failed", warnings

    # 規格 §4.2: single_source_failed / tier1_partial_failed → continue_with_warning
    for r in results:
        if r.status != "ok":
            warnings.append({
                "type": "source_failed",
                "source_id": r.source_id,
                "message": f"{r.source_id} failed: {r.error}",
            })
        # 規格 §4.1: consecutive_failures >= 3 觸發告警
        if r.consecutive_failures >= alert_after:
            warnings.append({
                "type": "source_failed",
                "source_id": r.source_id,
                "message": (
                    f"{r.source_id} has failed {r.consecutive_failures} times in a row."
                ),
            })

    return ("partial" if failed_ids else "ok", warnings)


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def write_raw(out_dir: Path, source_id: str, raw: bytes) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{source_id}.xml"
    path.write_bytes(raw)
    return path


def write_health_log(out_dir: Path, results: list[FetchResult]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "feed_health.json"
    path.write_text(
        json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def report_date_str(now: Optional[datetime] = None) -> str:
    return (now or datetime.now(TAIPEI)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch RSS feeds for daily report.")
    parser.add_argument("--feeds", type=Path, default=DEFAULT_FEEDS)
    parser.add_argument("--out-base", type=Path, default=DEFAULT_OUT_BASE)
    parser.add_argument("--date", type=str, default=None, help="Report date YYYY-MM-DD (Asia/Taipei)")
    parser.add_argument("--only", type=str, default=None, help="Comma-separated source_ids")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--max-workers", type=int, default=8)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    config = load_feeds(args.feeds)
    sources = config["sources"]

    if args.only:
        wanted = {x.strip() for x in args.only.split(",")}
        sources = [s for s in sources if s["source_id"] in wanted]

    enabled = [s for s in sources if s.get("enabled", True)]
    if not enabled:
        LOG.error("No enabled sources to fetch.")
        return 2

    date = args.date or report_date_str()
    out_dir = args.out_base / date

    LOG.info("Fetching %d sources to %s", len(enabled), out_dir)
    fetched, _state = fetch_all(enabled, args.timeout, args.retries, args.max_workers)

    for result, raw in fetched:
        if raw is not None:
            write_raw(out_dir, result.source_id, raw)

    results = [r for r, _ in fetched]
    health_path = write_health_log(out_dir, results)

    overall, warnings = decide_overall_status(results, enabled)

    LOG.info(
        "Status: %s (%d ok, %d failed, %d warnings) → %s",
        overall,
        sum(1 for r in results if r.status == "ok"),
        sum(1 for r in results if r.status != "ok"),
        len(warnings),
        health_path,
    )
    for w in warnings:
        LOG.warning("[%s] %s", w["type"], w["message"])

    if overall == "failed":
        LOG.error("All enabled sources failed; not producing a report.")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
