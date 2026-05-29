"""Local RSS fetch → git push script.

Dual-layer source strategy:
    1. Run fetch_rss locally (all 26 sources reachable from home IP)
    2. Commit raw XML + feed_health.json to git
    3. Push so the remote Claude routine can use --skip-fetch

Usage:
    python scripts/local_fetch.py                  # Today (Asia/Taipei)
    python scripts/local_fetch.py --date 2026-05-29
    python scripts/local_fetch.py --no-push        # Fetch + commit only
"""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

LOG = logging.getLogger("local_fetch")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TAIPEI = timezone(timedelta(hours=8))


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    LOG.info("$ %s", " ".join(cmd))
    return subprocess.run(cmd, cwd=PROJECT_ROOT, check=True, **kwargs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local fetch + git push for remote pipeline")
    parser.add_argument("--date", type=str, default=None, help="YYYY-MM-DD (default: today Asia/Taipei)")
    parser.add_argument("--no-push", action="store_true", help="Commit but don't push")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    date = args.date or datetime.now(TAIPEI).strftime("%Y-%m-%d")
    raw_dir = PROJECT_ROOT / "data" / "raw" / date

    # --- Step 1: fetch ---
    LOG.info("=== Step 1: fetch_rss (date=%s) ===", date)
    try:
        _run([sys.executable, "-m", "src.fetch_rss", "--date", date])
    except subprocess.CalledProcessError as e:
        LOG.error("fetch_rss failed with exit code %d", e.returncode)
        return e.returncode

    # Verify output
    xml_files = list(raw_dir.glob("*.xml"))
    health_file = raw_dir / "feed_health.json"
    if not xml_files:
        LOG.error("No XML files produced in %s", raw_dir)
        return 2

    LOG.info("Fetched %d XML files + feed_health.json", len(xml_files))

    # --- Step 2: git add + commit ---
    LOG.info("=== Step 2: git commit ===")
    files_to_add = [str(f.relative_to(PROJECT_ROOT)) for f in xml_files]
    if health_file.exists():
        files_to_add.append(str(health_file.relative_to(PROJECT_ROOT)))

    try:
        _run(["git", "add"] + files_to_add)

        # Check if there's anything to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=PROJECT_ROOT,
        )
        if result.returncode == 0:
            LOG.info("No changes to commit (raw data already up to date)")
        else:
            _run([
                "git", "commit",
                "-m", f"data: local fetch raw RSS for {date}\n\n{len(xml_files)} XML files from local machine.",
            ])
            LOG.info("Committed raw data for %s", date)
    except subprocess.CalledProcessError as e:
        LOG.error("Git commit failed: %s", e)
        return 1

    # --- Step 3: push ---
    if args.no_push:
        LOG.info("--no-push: skipping push")
        return 0

    LOG.info("=== Step 3: git push ===")
    try:
        _run(["git", "push"])
    except subprocess.CalledProcessError as e:
        LOG.error("Git push failed: %s", e)
        return 1

    LOG.info("Done. Remote routine can now use --skip-fetch for %s", date)
    return 0


if __name__ == "__main__":
    sys.exit(main())
