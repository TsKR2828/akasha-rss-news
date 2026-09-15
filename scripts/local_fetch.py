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
import os
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


def _toast(title: str, body: str) -> None:
    """彈 Windows 通知（best-effort）。桌面告警檔堆了 9 張才被看到（2026-09-15 事故），
    通知失敗不影響主流程——告警檔仍是最終防線。"""
    # 借用 PowerShell 已註冊的 AppID，免安裝任何模組即可在 Win10 顯示 toast
    ps_script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
        "ContentType = WindowsRuntime] | Out-Null;"
        "$t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
        "[Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
        "$n = $t.GetElementsByTagName('text');"
        "$n.Item(0).AppendChild($t.CreateTextNode($env:AK_TOAST_TITLE)) | Out-Null;"
        "$n.Item(1).AppendChild($t.CreateTextNode($env:AK_TOAST_BODY)) | Out-Null;"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
        "'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe'"
        ").Show([Windows.UI.Notifications.ToastNotification]::new($t))"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            env={**os.environ, "AK_TOAST_TITLE": title, "AK_TOAST_BODY": body},
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        LOG.warning("Windows 通知彈出失敗（告警檔仍會寫入）")


def _alert(date: str, message: str) -> None:
    """Push 失敗時在桌面放告警檔，讓月月隔天一眼看到（2026-06-30 起 push 靜默失敗 11 天的教訓）。"""
    LOG.error(message)
    alert_file = Path.home() / "Desktop" / f"AKASHA-PUSH-FAILED-{date}.txt"
    try:
        alert_file.write_text(
            f"akasha-local-fetch 於 {datetime.now(TAIPEI):%Y-%m-%d %H:%M} push 失敗\n\n"
            f"{message}\n\n"
            "處置：開 Claude Code 視窗說「akasha local fetch push 失敗，幫我看」。\n"
            "raw 資料已 commit 在本機 main，不會丟，修好 push 即可。\n",
            encoding="utf-8",
        )
    except OSError:
        LOG.error("告警檔寫入失敗: %s", alert_file)
    _toast(
        "阿卡夏館報 push 失敗",
        f"{date} 本機 fetch push 不出去，桌面有告警檔。開 Claude Code 說「akasha push 失敗幫我看」。",
    )


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
    # fetch_warnings.json 不 commit 的話會留成 untracked，之後雲端補抓同日期時
    # rebase 會被 untracked 檔案擋下（2026-09-07 起 push 連斷 9 天的成因之一）
    warnings_file = raw_dir / "fetch_warnings.json"
    if warnings_file.exists():
        files_to_add.append(str(warnings_file.relative_to(PROJECT_ROOT)))

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

    LOG.info("=== Step 3: git pull --rebase + push ===")
    # 遠端 main 常有雲端 session 的新 commit；不先 rebase 的話 push 會被
    # non-fast-forward 拒絕（2026-06-30 ~ 07-10 連續 11 天靜默失敗的根因）。
    # --autostash：工作區常有待審的 unstaged 修改，沒有它 rebase 會直接拒跑
    # （2026-07-11 告警檔實測 exit 128）。
    try:
        _run(["git", "pull", "--rebase", "--autostash", "origin", "main"])
    except subprocess.CalledProcessError as e:
        subprocess.run(["git", "rebase", "--abort"], cwd=PROJECT_ROOT)
        _alert(date, f"git pull --rebase origin main 失敗（可能有衝突）: {e}")
        return 1

    try:
        _run(["git", "push"])
    except subprocess.CalledProcessError as e:
        _alert(date, f"git push failed: {e}")
        return 1

    LOG.info("Done. Remote routine can now use --skip-fetch for %s", date)
    return 0


if __name__ == "__main__":
    sys.exit(main())
