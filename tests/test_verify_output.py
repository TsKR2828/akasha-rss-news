"""CARD-11：tests/test_verify_output.py

驗證 scripts/verify_output.py 的守門邏輯。

測試案例：
(a) 合規 report fixture → exit 0
(b) 塞一則 281 字 X post 且 status:'ok' → exit 1 且訊息含 event_id
(c) voice_text 含 URL → exit 1
(d) tw_highlight=true 但 tw_highlight_reason 為空 → exit 1
(e) schema 驗證失敗（缺必要欄位）→ exit 1
(f) --date 模式，六件套存在時 → exit 0（以 tmp_path 模擬輸出目錄）
(g) --date 模式，六件套缺少一個 → exit 1
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

# 被測對象
from scripts.verify_output import main, verify_report

# 專案根（用於 subprocess 模式的 cwd 與腳本路徑）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = _PROJECT_ROOT / "scripts" / "verify_output.py"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def source_ref() -> dict:
    return {
        "source_id": "bbc_world",
        "name": "BBC World",
        "publisher": "BBC",
        "title": "Test headline",
        "url": "https://www.bbc.com/news/test-12345",
        "published_at": "2026-06-11T05:00:00+08:00",
    }


@pytest.fixture
def claim(source_ref) -> dict:
    return {
        "claim": "事件核心事實已由兩個來源確認。",
        "source_id": source_ref["source_id"],
        "source_title": source_ref["title"],
        "source_url": source_ref["url"],
        "support_type": "direct",
    }


@pytest.fixture
def compliant_item(source_ref, claim) -> dict:
    """完全合規的 platform_output item（雙來源，無違規）。"""
    source_ref2 = {**source_ref, "source_id": "reuters_world", "publisher": "Reuters",
                   "url": "https://www.reuters.com/world/test-12345"}
    claim2 = {**claim, "source_id": "reuters_world", "source_url": source_ref2["url"]}
    return {
        "event_id": "daily_20260611_evt_001",
        "headline": "測試合規標題",
        "context": "這是脈絡說明，兩個 Tier-1 來源確認。",
        "beat": "INTL",
        "thread_text": "X 版內文，不超過 280 字。",
        "threads_text": "Threads 版內文，不超過 500 字。",
        "voice_text": "朗讀版內文，沒有網址與特殊符號。",
        "platform_outputs": {
            "x": {"max_chars": 280, "posts": ["X 版貼文內容，不超過 280 字。"]},
            "threads": {"max_chars": 500, "posts": ["Threads 版貼文，不超過 500 字。"]},
            "voice": {"text": "朗讀版內文，沒有網址與特殊符號。"},
        },
        "sources": [source_ref, source_ref2],
        "source_count": 2,
        "confidence": "high",
        "claim_trace": [claim, claim2],
        "tw_highlight": False,
        "selection_score": 80,
        "selection_reason": "多來源 Tier-1 確認。",
        "opinion_level": "none",
    }


@pytest.fixture
def compliant_report(compliant_item) -> dict:
    """完全合規的 report dict，status='ok'，無任何違規。"""
    return {
        "reportId": "daily_20260611",
        "date": "2026-06-11",
        "timezone": "Asia/Taipei",
        "generated_at": "2026-06-11T06:00:00+08:00",
        "status": "ok",
        "warnings": [],
        "sections": [
            {
                "beat": "INTL",
                "title": "國際大事",
                "emoji": "🌍",
                "items": [compliant_item],
            },
        ],
        "stats": {
            "total_feeds_checked": 28,
            "total_feeds_failed": 0,
            "total_feeds_failed_remote_blocked": 0,
            "total_articles_fetched": 300,
            "total_articles_after_filter": 150,
            "total_events_merged": 50,
            "total_events_selected": 10,
            "tw_highlights_count": 0,
        },
    }


# ---------------------------------------------------------------------------
# 輔助：把 report 寫入 tmp_path 並構造六件套
# ---------------------------------------------------------------------------

def _write_report_file(tmp_path: Path, report: dict) -> Path:
    """把 report dict 寫成 JSON 檔案，回傳路徑。"""
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    return path


def _create_six_piece_suite(output_base: Path, date_str: str) -> None:
    """在 output_base 下建立六件套空白檔案（模擬實際輸出存在）。"""
    dc = date_str.replace("-", "")
    (output_base / "platforms").mkdir(parents=True, exist_ok=True)
    (output_base / "logs").mkdir(parents=True, exist_ok=True)
    for path in [
        output_base / f"daily_{dc}.json",
        output_base / f"daily_{dc}.md",
        output_base / f"voice_{dc}.txt",
        output_base / "platforms" / f"x_{dc}.json",
        output_base / "platforms" / f"threads_{dc}.json",
        output_base / "logs" / f"run_{dc}.json",
    ]:
        path.write_text("{}", encoding="utf-8")


# ---------------------------------------------------------------------------
# (a) 合規 report → verify_report 回傳空 list（即 exit 0）
# ---------------------------------------------------------------------------

class TestCompliantReport:
    def test_compliant_report_has_no_issues(self, compliant_report):
        """合規 report 不得回傳任何問題。"""
        issues = verify_report(compliant_report)
        assert issues == [], f"預期無問題，但得到：{issues}"

    def test_main_returns_zero_for_compliant_report(self, tmp_path, compliant_report):
        """合規 report 以 --report-file 模式執行應 exit 0。"""
        path = _write_report_file(tmp_path, compliant_report)
        result = main(["--report-file", str(path)])
        assert result == 0


# ---------------------------------------------------------------------------
# (b) 281 字 X post + status:'ok' → exit 1，訊息含 event_id
# ---------------------------------------------------------------------------

class TestXPostOverLimit:
    def test_x_post_281_chars_exits_one(self, tmp_path, compliant_report):
        """X post 超 280 字且 status='ok' 應 exit 1。"""
        bad_report = copy.deepcopy(compliant_report)
        # 塞進一則 281 字的 X post
        bad_report["sections"][0]["items"][0]["platform_outputs"]["x"]["posts"] = ["x" * 281]
        path = _write_report_file(tmp_path, bad_report)
        result = main(["--report-file", str(path)])
        assert result == 1

    def test_x_post_281_chars_message_contains_event_id(self, compliant_report):
        """違規訊息必須含 event_id，方便排查。"""
        bad_report = copy.deepcopy(compliant_report)
        eid = bad_report["sections"][0]["items"][0]["event_id"]
        bad_report["sections"][0]["items"][0]["platform_outputs"]["x"]["posts"] = ["x" * 281]
        issues = verify_report(bad_report)
        assert any(eid in issue for issue in issues), (
            f"找不到含 event_id '{eid}' 的問題訊息，實際問題：{issues}"
        )

    def test_status_ok_with_violation_is_itself_a_failure(self, compliant_report):
        """status='ok' 但有違規 → 自我一致性檢查也應算一條失敗。"""
        bad_report = copy.deepcopy(compliant_report)
        bad_report["sections"][0]["items"][0]["platform_outputs"]["x"]["posts"] = ["x" * 281]
        bad_report["status"] = "ok"  # 故意保持 ok
        issues = verify_report(bad_report)
        # 必有 x post 超長問題
        assert any("281" in issue or "X post" in issue for issue in issues)
        # 必有 status 矛盾問題
        assert any("ok" in issue and ("矛盾" in issue or "status" in issue or "partial" in issue or "違規" in issue)
                   for issue in issues), f"應有 status 矛盾問題，實際：{issues}"


# ---------------------------------------------------------------------------
# (c) voice_text 含 URL → exit 1
# ---------------------------------------------------------------------------

class TestVoiceTextWithUrl:
    def test_voice_text_with_url_exits_one(self, tmp_path, compliant_report):
        """voice_text 含 URL 應 exit 1。"""
        bad_report = copy.deepcopy(compliant_report)
        bad_report["sections"][0]["items"][0]["voice_text"] = (
            "詳情請見 https://bbc.com/news/12345 報導。"
        )
        # schema 層也會擋，先把 platform_outputs.voice.text 同步（否則 schema 先報錯）
        bad_report["sections"][0]["items"][0]["platform_outputs"]["voice"]["text"] = (
            "詳情請見 https://bbc.com/news/12345 報導。"
        )
        # status 改 partial 讓 status 一致性不蓋過真正問題
        bad_report["status"] = "partial"
        path = _write_report_file(tmp_path, bad_report)
        result = main(["--report-file", str(path)])
        assert result == 1

    def test_voice_text_url_produces_issue_message(self, compliant_report):
        """voice_text URL 問題訊息應可識別。"""
        bad_report = copy.deepcopy(compliant_report)
        bad_report["sections"][0]["items"][0]["voice_text"] = (
            "詳情見 https://example.com 報導。"
        )
        bad_report["sections"][0]["items"][0]["platform_outputs"]["voice"]["text"] = (
            "詳情見 https://example.com 報導。"
        )
        bad_report["status"] = "partial"
        issues = verify_report(bad_report)
        assert issues, "voice_text 含 URL 應產生至少一條問題"


# ---------------------------------------------------------------------------
# (d) tw_highlight=true 但 tw_highlight_reason 為空 → exit 1
# ---------------------------------------------------------------------------

class TestTwHighlightReason:
    def test_tw_highlight_true_without_reason_exits_one(self, tmp_path, compliant_report):
        """tw_highlight=true 但缺 tw_highlight_reason 應 exit 1。"""
        bad_report = copy.deepcopy(compliant_report)
        bad_report["sections"][0]["items"][0]["tw_highlight"] = True
        bad_report["sections"][0]["items"][0]["tw_highlight_reason"] = ""
        bad_report["status"] = "partial"
        path = _write_report_file(tmp_path, bad_report)
        result = main(["--report-file", str(path)])
        assert result == 1

    def test_tw_highlight_true_with_reason_passes(self, compliant_report):
        """tw_highlight=true 且有 tw_highlight_reason 應無此問題。"""
        good_report = copy.deepcopy(compliant_report)
        good_report["sections"][0]["items"][0]["tw_highlight"] = True
        good_report["sections"][0]["items"][0]["tw_highlight_reason"] = (
            "涉及台灣半導體供應鏈。"
        )
        issues = verify_report(good_report)
        tw_issues = [i for i in issues if "tw_highlight_reason" in i]
        assert tw_issues == [], f"有 reason 時不應有 tw_highlight_reason 問題：{tw_issues}"


# ---------------------------------------------------------------------------
# (e) schema 驗證失敗（缺必要欄位）
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_missing_required_field_exits_one(self, tmp_path, compliant_report):
        """缺少 schema 必要欄位應 exit 1。"""
        bad_report = copy.deepcopy(compliant_report)
        del bad_report["reportId"]  # 刪除必要欄位
        path = _write_report_file(tmp_path, bad_report)
        result = main(["--report-file", str(path)])
        assert result == 1

    def test_invalid_status_enum_exits_one(self, tmp_path, compliant_report):
        """status 不在 enum 中應 exit 1。"""
        bad_report = copy.deepcopy(compliant_report)
        bad_report["status"] = "success"  # invalid enum value
        path = _write_report_file(tmp_path, bad_report)
        result = main(["--report-file", str(path)])
        assert result == 1


# ---------------------------------------------------------------------------
# (f)(g) --date 模式，六件套存在 → exit 0；缺一個 → exit 1
# ---------------------------------------------------------------------------

class TestDateModeSixPieceSuite:
    def test_date_mode_all_six_present_exits_zero(self, tmp_path, compliant_report):
        """--date 模式，六件套齊全且 report 合規 → exit 0。"""
        date_str = "2026-06-11"
        dc = date_str.replace("-", "")
        output_base = tmp_path / "output"
        output_base.mkdir()
        _create_six_piece_suite(output_base, date_str)
        # 用合規 report 覆寫 daily_*.json
        (output_base / f"daily_{dc}.json").write_text(
            json.dumps(compliant_report, ensure_ascii=False), encoding="utf-8"
        )
        result = main(["--date", date_str, "--output-base", str(output_base)])
        assert result == 0

    def test_date_mode_missing_one_file_exits_one(self, tmp_path, compliant_report):
        """--date 模式，六件套缺少一個 → exit 1。"""
        date_str = "2026-06-11"
        dc = date_str.replace("-", "")
        output_base = tmp_path / "output"
        output_base.mkdir()
        _create_six_piece_suite(output_base, date_str)
        # 刪除 voice 檔
        (output_base / f"voice_{dc}.txt").unlink()
        # 用合規 report 覆寫 daily_*.json
        (output_base / f"daily_{dc}.json").write_text(
            json.dumps(compliant_report, ensure_ascii=False), encoding="utf-8"
        )
        result = main(["--date", date_str, "--output-base", str(output_base)])
        assert result == 1


# ---------------------------------------------------------------------------
# 邊界：Threads 貼文超 500 字
# ---------------------------------------------------------------------------

class TestThreadsPostOverLimit:
    def test_threads_post_501_chars_exits_one(self, tmp_path, compliant_report):
        """Threads post 超 500 字應 exit 1。"""
        bad_report = copy.deepcopy(compliant_report)
        bad_report["sections"][0]["items"][0]["platform_outputs"]["threads"]["posts"] = [
            "t" * 501
        ]
        bad_report["status"] = "partial"
        path = _write_report_file(tmp_path, bad_report)
        result = main(["--report-file", str(path)])
        assert result == 1


# ---------------------------------------------------------------------------
# subprocess CLI 煙霧測試：鎖死「文件指定的 CLI 入口可用」
# 以 `python scripts/verify_output.py` 方式直跑（非 pytest in-process），
# 防止 script-mode sys.path 自舉失敗導致守門腳本在實際使用時靜默崩潰。
# ---------------------------------------------------------------------------

def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    """以 `python scripts/verify_output.py <args>` 方式直跑腳本（script-mode）。

    cwd 固定在專案根，確保環境與 Routine push 前的實際用法一致。
    """
    cmd = [sys.executable, str(_SCRIPT_PATH)] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(_PROJECT_ROOT),
    )


class TestSubprocessCliSmokeTests:
    """用 subprocess 直跑腳本，確認 script-mode 的 sys.path 自舉正常。

    這組測試是 in-process 測試的補充：pytest 環境中 conftest.py 會自動注入
    PROJECT_ROOT 到 sys.path，恰好遮蔽 script-mode 的 import 失敗。
    只有用 subprocess 才能暴露真實的 CLI 入口可用性。
    """

    def test_subprocess_compliant_report_returns_zero(self, tmp_path, compliant_report):
        """合規 report 以 `python scripts/verify_output.py --report-file` 直跑應 exit 0。

        驗收條件 #1：合規輸入的 CLI 入口可用（exit 0、不崩潰）。
        """
        path = _write_report_file(tmp_path, compliant_report)
        proc = _run_cli(["--report-file", str(path)])
        assert proc.returncode == 0, (
            f"合規 report 期望 exit 0，實際 exit {proc.returncode}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )
        assert "PASS" in proc.stdout, (
            f"合規 report 期望 stdout 含 'PASS'，實際：{proc.stdout}"
        )

    def test_subprocess_281_char_x_post_with_status_ok_returns_one_with_event_id(
        self, tmp_path, compliant_report
    ):
        """281 字 X post + status:'ok' 以直跑方式應 exit 1 且 stdout 含 event_id。

        驗收條件 #2：歷史 06-11 事故型態（281 字 + status:ok）必須被守門腳本偵測到，
        且輸出含 event_id 以利排查。此測試確保守門腳本在文件指定的 CLI 入口下確實
        攔截，而非只是因為未捕捉例外而恰好 exit 1。
        """
        bad_report = copy.deepcopy(compliant_report)
        eid = bad_report["sections"][0]["items"][0]["event_id"]
        bad_report["sections"][0]["items"][0]["platform_outputs"]["x"]["posts"] = ["x" * 281]
        bad_report["status"] = "ok"  # 故意保留 ok，模擬 06-11 事故
        path = _write_report_file(tmp_path, bad_report)
        proc = _run_cli(["--report-file", str(path)])
        assert proc.returncode == 1, (
            f"281 字 X post + status:ok 期望 exit 1，實際 exit {proc.returncode}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )
        assert eid in proc.stdout, (
            f"期望 stdout 含 event_id '{eid}'（方便排查）\n"
            f"實際 stdout：{proc.stdout}\nstderr: {proc.stderr}"
        )
