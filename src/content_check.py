"""改寫後內容檢查（只警告，不擋出報）。

2026-09-26 改善研究：雲端 agent 直接改寫事件欄位，程式原本的改寫後檢查
（claim_trace 修正、禁用詞、lint 紀錄）在正式流程中完全沒跑；
verify_output 只看格式，所以「標題還是英文」「貼文空白」「數字對不上來源」
「把巴基斯坦的說法寫成塔利班的」都照常發出去。

月月決定（2026-09-26）：新的內容檢查先「只警告」跑 7 天，看誤報多寡再決定
哪些升級成擋住不發。所以本模組：
- 不修改任何事件或輸出檔
- 不寫進讀者看得到的館報 warnings（不讓館報狀態變 partial）
- 結果寫到 data/events/{date}/_content_check.json，隨 daily-reports 推送，
  Routine 在完成回報裡列出提醒則數（月月手機會收到推播）

檢查項目：
- untranslated        標題沒有中文（沒改寫到）
- empty_field         thread_text / threads_text / voice_text 空白
- banned_phrase       規格 §13 禁用詞
- filler_phrase       評論來源多寡的套話（「細節不多」「只有單一消息來源」…）
- trace_url_mismatch  claim_trace 的網址不在該則的來源清單裡
- confidence_overclaim  標「高可信度」但只有一家媒體
- number_not_in_source  改寫文字裡的數字在來源標題/摘要找不到（人工抽查短名單）
- weekday_mismatch    「9月20日週六」這類日期與星期對不上

CLI：
    python -m src.content_check --date 2026-09-26
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import date as date_cls, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from src.outlets import outlet_count
from src.validators import BANNED_PHRASES

LOG = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVENTS_BASE = PROJECT_ROOT / "data" / "events"
TAIPEI = timezone(timedelta(hours=8))

TEXT_FIELDS = ("headline", "context", "thread_text", "threads_text", "voice_text")
REQUIRED_TEXT_FIELDS = ("thread_text", "threads_text", "voice_text")

# 評論「來源多寡」的套話：規則要求保留語氣放在事實句本身（據報導、○○表示），
# 不另外評論來源數量（QUAL-5：09-17~09-25 約 14% 的新聞帶這類句子）
FILLER_PHRASES = [
    "細節不多",
    "細節有限",
    "更多細節",
    "尚未透露",
    "單一消息來源",
    "單一來源",
    "只有一家",
    "目前只有",
    "其他媒體尚未",
    "尚待其他",
]

_CJK_RE = re.compile(r"[一-鿿]")
# 數字：123、1,234、3.5、11.2萬 的數字部分
_NUM_RE = re.compile(r"(?<![\d.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)")
# 日期/時間/序數用的數字不比對（9月20日、第3季、10點）
_NUM_SKIP_AFTER = ("月", "日", "年", "時", "點", "分", "號", "歲", "週", "世紀")
_NUM_SKIP_BEFORE = ("第",)
_WEEKDAY_RE = re.compile(
    r"(\d{1,2})月(\d{1,2})日[（(]?(?:星期|週|禮拜)([一二三四五六日天])"
)
_WEEKDAY_ZH = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}


def _source_text(event: dict) -> str:
    parts = []
    for s in event.get("sources", []):
        parts.append(s.get("title") or "")
        parts.append(s.get("summary") or "")
    return " ".join(parts)


def _numbers(text: str) -> list[str]:
    found = []
    for m in _NUM_RE.finditer(text or ""):
        after = text[m.end():m.end() + 2]
        before = text[max(0, m.start() - 1):m.start()]
        if after.startswith(_NUM_SKIP_AFTER) or before in _NUM_SKIP_BEFORE:
            continue
        found.append(m.group(1))
    return found


def _norm_num(n: str) -> str:
    n = n.replace(",", "")
    if "." in n:
        n = n.rstrip("0").rstrip(".")
    return n


def _source_numbers(source_text: str) -> set[str]:
    return {_norm_num(n) for n in _NUM_RE.findall(source_text)}


def _check_weekdays(text: str, report_date: date_cls) -> list[str]:
    problems = []
    for m in _WEEKDAY_RE.finditer(text or ""):
        month, day, wd = int(m.group(1)), int(m.group(2)), m.group(3)
        # 取離館報日期最近的年份（跨年時 12 月/1 月）
        candidates = []
        for year in (report_date.year - 1, report_date.year, report_date.year + 1):
            try:
                candidates.append(date_cls(year, month, day))
            except ValueError:
                continue
        if not candidates:
            continue
        actual = min(candidates, key=lambda d: abs((d - report_date).days))
        if actual.weekday() != _WEEKDAY_ZH[wd]:
            problems.append(
                f"「{m.group(0)}」：{actual.isoformat()} 其實是星期"
                f"{'一二三四五六日'[actual.weekday()]}"
            )
    return problems


def check_event(event: dict, report_date: date_cls) -> list[dict]:
    """檢查一則改寫後事件，回傳提醒清單（不修改事件）。"""
    eid = event.get("event_id", "?")
    headline = event.get("headline", "")
    issues: list[dict] = []

    def add(kind: str, detail: str) -> None:
        issues.append({"event_id": eid, "headline": headline, "type": kind, "detail": detail})

    if headline and not _CJK_RE.search(headline):
        add("untranslated", "標題沒有中文，可能沒有改寫到")

    for field in REQUIRED_TEXT_FIELDS:
        if not (event.get(field) or "").strip():
            add("empty_field", f"{field} 空白")

    for field in TEXT_FIELDS:
        text = event.get(field) or ""
        for phrase in BANNED_PHRASES:
            if phrase in text:
                add("banned_phrase", f"{field} 含禁用詞「{phrase}」")
        for phrase in FILLER_PHRASES:
            if phrase in text:
                add("filler_phrase", f"{field} 含套話「{phrase}」")

    source_urls = {s.get("url") for s in event.get("sources", []) if s.get("url")}
    for i, ct in enumerate(event.get("claim_trace") or []):
        url = ct.get("source_url")
        if url and url not in source_urls:
            add("trace_url_mismatch", f"claim_trace[{i}] 網址不在來源清單：{url}")

    if event.get("confidence") == "high" and outlet_count(event.get("sources", [])) < 2:
        add("confidence_overclaim", "標高可信度，但來源只有一家媒體（出報時已降為中）")

    src_nums = _source_numbers(_source_text(event))
    rewritten = " ".join(event.get(f) or "" for f in ("headline", "context", "voice_text"))
    missing = []
    for n in _numbers(rewritten):
        key = _norm_num(n)
        if key not in src_nums and key not in missing:
            missing.append(key)
    if missing:
        add("number_not_in_source",
            f"這些數字在來源標題/摘要找不到（可能是單位換算，請人工抽查）：{', '.join(missing)}")

    for field in TEXT_FIELDS:
        for problem in _check_weekdays(event.get(field) or "", report_date):
            add("weekday_mismatch", f"{field} {problem}")

    return issues


def run_content_check(events: list[dict], date_str: str) -> dict:
    report_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    issues: list[dict] = []
    for e in events:
        issues.extend(check_event(e, report_date))
    by_type: dict[str, int] = {}
    for it in issues:
        by_type[it["type"]] = by_type.get(it["type"], 0) + 1
    return {
        "date": date_str,
        "generated_at": datetime.now(TAIPEI).isoformat(),
        "mode": "warn_only",
        "summary": {
            "events_checked": len(events),
            "events_flagged": len({it["event_id"] for it in issues}),
            "issues": len(issues),
            "by_type": by_type,
        },
        "issues": issues,
    }


def write_content_check(events: list[dict], date_str: str, events_dir: Path) -> dict:
    result = run_content_check(events, date_str)
    events_dir.mkdir(parents=True, exist_ok=True)
    (events_dir / "_content_check.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    s = result["summary"]
    LOG.info("內容檢查（只警告）：%d 則事件中 %d 則有提醒，共 %d 條 %s",
             s["events_checked"], s["events_flagged"], s["issues"], s["by_type"])
    return result


def _load_selected_events(events_dir: Path) -> list[dict]:
    manifest_path = events_dir / "_selection_manifest.json"
    if not manifest_path.exists():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    events = []
    for eid in manifest.get("selected_event_ids", []):
        fp = events_dir / f"{eid}.json"
        if fp.exists():
            events.append(json.loads(fp.read_text(encoding="utf-8")))
    return events


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="改寫後內容檢查（只警告）")
    parser.add_argument("--events-base", type=Path, default=DEFAULT_EVENTS_BASE)
    parser.add_argument("--date", type=str, default=None)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    date = args.date or datetime.now(TAIPEI).strftime("%Y-%m-%d")
    events_dir = args.events_base / date
    events = _load_selected_events(events_dir)
    if not events:
        LOG.error("找不到 %s 的已選事件", date)
        return 1
    result = write_content_check(events, date, events_dir)
    for it in result["issues"]:
        print(f"[{it['type']}] {it['event_id']} {it['headline'][:30]}：{it['detail']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
