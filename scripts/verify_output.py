"""生產館報輸出守門腳本。

Routine 在每次 push 前必跑，用來確保生產輸出全面符合 P0 規格。
歷史背景：2026-06-11 健檢發現生產輸出在 push 前沒有任何強制驗證關卡
（警告鏈斷裂、status 可能與內容脫鉤），此腳本用來堵住這條缺口。
（健檢初版所稱「18 則 X 貼文超 280 / schema 18 錯」經覆核為編碼測量
誤差，已撤回；X 平台加權計數議題見 DECISIONS.md 2026-06-11 豁免決策。）

CLI 用法：
    python scripts/verify_output.py --date YYYY-MM-DD [--output-base PATH]
    python scripts/verify_output.py --report-file PATH

回傳碼：
    0 — 全部通過（印 PASS 摘要）
    1 — 至少一條違規（逐行列印問題）

對應規格：§11.2、§11.3、§12.3、§17.1、§17.2、§20.1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from jsonschema import Draft7Validator, RefResolver, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = PROJECT_ROOT / "schemas"

# script-mode 自舉：直跑 `python scripts/verify_output.py` 時 sys.path[0] 是
# scripts/，而非專案根，導致 `from src.*` 全部 ModuleNotFoundError。
# 這行確保不論用哪種方式呼叫都能找到 src.*（對照 conftest.py 第 6-7 行）。
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.validators import VOICE_FORBIDDEN_PATTERNS  # noqa: E402
from src.formatter import validate_report_output  # noqa: E402

# 預設輸出基礎目錄（與 formatter.py 一致）
DEFAULT_OUTPUT_BASE = PROJECT_ROOT / "output"


# ---------------------------------------------------------------------------
# Schema 載入（與 tests/test_schemas.py 既有寫法相同）
# ---------------------------------------------------------------------------

def _load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _make_report_validator() -> Draft7Validator:
    """建立能解析 $ref 的 report.schema.json 驗證器。

    照抄 tests/test_schemas.py 的 _validator_for_report 寫法。
    """
    report_schema = _load_schema("report.schema.json")
    all_schemas = {
        "article.schema.json": _load_schema("article.schema.json"),
        "event.schema.json": _load_schema("event.schema.json"),
        "platform_output.schema.json": _load_schema("platform_output.schema.json"),
        "report.schema.json": report_schema,
    }
    store = {schema["$id"]: schema for schema in all_schemas.values()}
    resolver = RefResolver.from_schema(report_schema, store=store)
    return Draft7Validator(report_schema, resolver=resolver)


# ---------------------------------------------------------------------------
# 六件套存在性確認（--date 模式專用）
# ---------------------------------------------------------------------------

def _check_six_piece_suite(date_str: str, output_base: Path) -> list[str]:
    """確認六件套輸出檔案存在。

    六件套：
        daily_YYYYMMDD.json / .md
        voice_YYYYMMDD.txt
        platforms/x_YYYYMMDD.json
        platforms/threads_YYYYMMDD.json
        logs/run_YYYYMMDD.json
    """
    dc = date_str.replace("-", "")
    expected = [
        output_base / f"daily_{dc}.json",
        output_base / f"daily_{dc}.md",
        output_base / f"voice_{dc}.txt",
        output_base / "platforms" / f"x_{dc}.json",
        output_base / "platforms" / f"threads_{dc}.json",
        output_base / "logs" / f"run_{dc}.json",
    ]
    errors: list[str] = []
    for path in expected:
        if not path.exists():
            errors.append(f"缺少六件套檔案：{path}")
    return errors


# ---------------------------------------------------------------------------
# P0 逐 item 檢查
# ---------------------------------------------------------------------------

def _check_items(report: dict) -> list[str]:
    """逐 item 執行 P0 檢查，回傳問題字串列表。

    檢查項：
    1. X post ≤ 280 字
    2. Threads post ≤ 500 字
    3. voice_text 過 VOICE_FORBIDDEN_PATTERNS
    4. claim_trace 非空
    5. headline 非空
    6. source_count==1 必有 single_source_warning=true
    7. tw_highlight=true 必有 tw_highlight_reason（非空字串）
    """
    issues: list[str] = []

    # 用既有的 validate_report_output 跑基本 P0（X/Threads 長度、voice lint、headline、claim_trace、single_source_warning）
    base_issues = validate_report_output(report)
    for item_issue in base_issues:
        issues.append(item_issue.get("message", str(item_issue)))

    # 補充 tw_highlight_reason 檢查（validate_report_output 未涵蓋）
    for section in report.get("sections", []):
        for item in section.get("items", []):
            eid = item.get("event_id", "?")
            if item.get("tw_highlight"):
                reason = item.get("tw_highlight_reason")
                if not reason or not str(reason).strip():
                    issues.append(
                        f"{eid}: tw_highlight=true 但 tw_highlight_reason 為空或缺失"
                    )

    return issues


# ---------------------------------------------------------------------------
# 自我一致性：status 與違規不得矛盾
# ---------------------------------------------------------------------------

def _check_status_consistency(report: dict, item_issues: list[str]) -> list[str]:
    """若 status='ok' 但查出違規，本身就是一條失敗。"""
    errors: list[str] = []
    status = report.get("status", "")
    if status == "ok" and item_issues:
        errors.append(
            f"report.status='ok' 但發現 {len(item_issues)} 條違規"
            "——status 應為 'partial' 或 'failed'"
        )
    return errors


# ---------------------------------------------------------------------------
# 主驗證流程
# ---------------------------------------------------------------------------

def verify_report(
    report: dict,
    date_str: Optional[str] = None,
    output_base: Optional[Path] = None,
) -> list[str]:
    """對一份 report dict 執行全部驗證，回傳所有問題字串。

    Args:
        report: 已解析的 report JSON dict
        date_str: 若提供，額外做六件套存在性確認
        output_base: 六件套確認的基礎目錄

    Returns:
        list[str] — 空 list 表示全部通過
    """
    all_issues: list[str] = []

    # 1. jsonschema 驗證（report.schema.json，含 $ref 解析）
    validator = _make_report_validator()
    try:
        validator.validate(report)
    except ValidationError as exc:
        all_issues.append(f"schema 驗證失敗：{exc.message} (path: {list(exc.absolute_path)})")

    # 2. 逐 item P0 檢查
    item_issues = _check_items(report)
    all_issues.extend(item_issues)

    # 3. 自我一致性（status 矛盾）
    all_issues.extend(_check_status_consistency(report, item_issues))

    # 4. 六件套存在性（僅 --date 模式）
    if date_str and output_base:
        all_issues.extend(_check_six_piece_suite(date_str, output_base))

    return all_issues


def _load_report_from_date(date_str: str, output_base: Path) -> Optional[dict]:
    """依日期從輸出目錄讀取主報告 JSON。"""
    dc = date_str.replace("-", "")
    path = output_base / f"daily_{dc}.json"
    if not path.exists():
        print(f"ERROR: 找不到主報告 JSON：{path}", file=sys.stderr)
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="驗證生產館報輸出是否符合 P0 規格（schema + 逐 item 檢查 + 一致性）。"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="驗證指定日期的輸出（從 --output-base 讀取主報告 + 六件套確認）",
    )
    mode.add_argument(
        "--report-file",
        metavar="PATH",
        type=Path,
        help="直接指定 report JSON 檔案路徑（不做六件套確認）",
    )
    parser.add_argument(
        "--output-base",
        metavar="PATH",
        type=Path,
        default=DEFAULT_OUTPUT_BASE,
        help=f"輸出目錄根（預設：{DEFAULT_OUTPUT_BASE}）",
    )
    args = parser.parse_args(argv)

    # 載入 report
    if args.date:
        report = _load_report_from_date(args.date, args.output_base)
        if report is None:
            return 1
        date_for_suite = args.date
        base_for_suite = args.output_base
    else:
        path = args.report_file
        if not path.exists():
            print(f"ERROR: 找不到報告檔案：{path}", file=sys.stderr)
            return 1
        report = json.loads(path.read_text(encoding="utf-8"))
        date_for_suite = None
        base_for_suite = None

    # 驗證
    issues = verify_report(
        report,
        date_str=date_for_suite,
        output_base=base_for_suite,
    )

    # 輸出
    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        print(f"\n共 {len(issues)} 條違規。")
        return 1

    # 通過
    item_count = sum(
        len(section.get("items", []))
        for section in report.get("sections", [])
    )
    print(f"PASS: 驗證通過。報告狀態={report.get('status', '?')}，{item_count} 則 items，無違規。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
