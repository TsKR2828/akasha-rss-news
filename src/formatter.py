"""Phase 4 — Multi-format output: JSON / Markdown / Voice / X / Threads + run log.

把 Phase 3 改寫完的 events 轉換成六種輸出檔：

    output/daily_YYYYMMDD.json              # 主報告 JSON（report.schema.json）
    output/daily_YYYYMMDD.md                # Markdown 可讀版
    output/voice_YYYYMMDD.txt               # 朗讀稿
    output/platforms/x_YYYYMMDD.json        # X 貼文草稿
    output/platforms/threads_YYYYMMDD.json  # Threads 貼文草稿
    output/logs/run_YYYYMMDD.json           # run log

對應規格：
- §11.2  report.schema.json
- §11.3  platform_output.schema.json
- §12.3  朗讀版規則
- §13.3  每日開場
- §13.4  區塊轉場語
- §13.5  來源宣告
- §17.1  輸出驗證
- §17.2  voice_text lint

CLI 用法：
    python -m src.formatter --date 2026-05-19
    python -m src.formatter --date 2026-05-19 --dry-run
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import yaml

LOG = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVENTS_BASE = PROJECT_ROOT / "data" / "events"
OUTPUT_BASE = PROJECT_ROOT / "output"
BEATS_PATH = PROJECT_ROOT / "config" / "beats.yaml"

TAIPEI = timezone(timedelta(hours=8))

# Beat 顯示順序（規格 §2.1）
BEAT_ORDER = ["INTL", "ARTS", "AI", "ECON", "PTS_LOCAL", "TW_STORY"]

# Beat metadata fallback（正常從 beats.yaml 載入）
BEAT_FALLBACK = {
    "INTL":      {"name": "國際大事",      "emoji": "🌍"},
    "ARTS":      {"name": "八大藝術",      "emoji": "🎭"},
    "AI":        {"name": "AI 新知",       "emoji": "🤖"},
    "ECON":      {"name": "全球經濟趨勢",  "emoji": "📊"},
    "PTS_LOCAL": {"name": "公視在地新聞",  "emoji": "🇹🇼"},
    "TW_STORY":  {"name": "台灣故事",      "emoji": "📜"},
}

# 區塊轉場語（規格 §13.4，每個 beat 取第一句作為預設）
BEAT_TRANSITIONS = {
    "INTL":      "先從世界的那一邊說起。",
    "ARTS":      "接下來，我們翻開藝術那一頁。",
    "AI":        "然後是 AI 的部分，這個領域最近沒有一天是安靜的。",
    "ECON":      "看看錢的世界發生了什麼。",
    "PTS_LOCAL": "回到台灣這邊。",
    "TW_STORY":  "最後，圖書館員想跟你分享一個台灣的故事。",
}

# 星期對照
WEEKDAY_ZH = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

# Platform 字數上限
X_MAX_CHARS = 280
THREADS_MAX_CHARS = 500


# ---------------------------------------------------------------------------
# Beat metadata loader
# ---------------------------------------------------------------------------

def load_beat_meta(path: Path = BEATS_PATH) -> dict[str, dict]:
    """載入 beats.yaml，回傳 {beat_id: {name, emoji}}。"""
    try:
        with path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        meta: dict[str, dict] = {}
        for beat_id, info in cfg.get("beats", {}).items():
            meta[beat_id] = {
                "name": info.get("name", beat_id),
                "emoji": info.get("emoji", ""),
            }
        for mark_id, info in cfg.get("special_marks", {}).items():
            if mark_id not in meta:
                meta[mark_id] = {
                    "name": info.get("name", mark_id),
                    "emoji": info.get("emoji", ""),
                }
        return meta
    except Exception as e:
        LOG.warning("無法載入 beats.yaml: %s，使用 fallback", e)
        return dict(BEAT_FALLBACK)


# ---------------------------------------------------------------------------
# Text splitting（把長文切成不超過 max_chars 的 posts）
# ---------------------------------------------------------------------------

def split_posts(text: str, max_chars: int) -> list[str]:
    """把文字切成 ≤ max_chars 的 posts。

    切分邏輯：
    1. 先嘗試以句號/。/！/？ 為切點
    2. 若單句超限，退而以逗號/、/， 切
    3. 最後強制按 max_chars 截斷
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    # 以中文/英文句末標點切句
    sentences = re.split(r"(?<=[。！？.!?])\s*", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    posts: list[str] = []
    current = ""

    for sent in sentences:
        if not current:
            if len(sent) <= max_chars:
                current = sent
            else:
                # 單句超長，需要二次切分
                sub_posts = _split_long_sentence(sent, max_chars)
                posts.extend(sub_posts[:-1])
                current = sub_posts[-1] if sub_posts else ""
        elif len(current) + len(sent) + 1 <= max_chars:
            current = current + sent
        else:
            posts.append(current)
            if len(sent) <= max_chars:
                current = sent
            else:
                sub_posts = _split_long_sentence(sent, max_chars)
                posts.extend(sub_posts[:-1])
                current = sub_posts[-1] if sub_posts else ""

    if current:
        posts.append(current)

    return posts


def _split_long_sentence(text: str, max_chars: int) -> list[str]:
    """切分超長句子：先試逗號，再強制截斷。"""
    if len(text) <= max_chars:
        return [text]

    # 嘗試以逗號/、切分
    parts = re.split(r"(?<=[，、,])\s*", text)
    if len(parts) > 1:
        result: list[str] = []
        current = ""
        for part in parts:
            if not current:
                current = part
            elif len(current) + len(part) <= max_chars:
                current = current + part
            else:
                result.append(current)
                current = part
        if current:
            result.append(current)
        # 遞迴處理仍超長的部分
        final: list[str] = []
        for r in result:
            if len(r) > max_chars:
                final.extend(_force_split(r, max_chars))
            else:
                final.append(r)
        return final

    return _force_split(text, max_chars)


def _force_split(text: str, max_chars: int) -> list[str]:
    """強制按字數截斷。"""
    posts = []
    while len(text) > max_chars:
        posts.append(text[:max_chars])
        text = text[max_chars:]
    if text:
        posts.append(text)
    return posts


# ---------------------------------------------------------------------------
# Platform output item builder
# ---------------------------------------------------------------------------

def build_platform_output_item(event: dict) -> dict:
    """把改寫後的 event 轉成 platform_output.schema.json 格式。"""
    thread_text = event.get("thread_text", "")
    threads_text = event.get("threads_text", "")
    voice_text = event.get("voice_text", "")

    x_posts = split_posts(thread_text, X_MAX_CHARS)
    threads_posts = split_posts(threads_text, THREADS_MAX_CHARS)

    item = {
        "event_id": event.get("event_id", ""),
        "headline": event.get("headline", ""),
        "context": event.get("context", ""),
        "beat": event.get("beat", ""),
        "thread_text": thread_text,
        "threads_text": threads_text,
        "voice_text": voice_text,
        "platform_outputs": {
            "x": {
                "max_chars": X_MAX_CHARS,
                "posts": x_posts,
            },
            "threads": {
                "max_chars": THREADS_MAX_CHARS,
                "posts": threads_posts,
            },
            "voice": {
                "text": voice_text,
            },
        },
        "sources": event.get("sources", []),
        "source_count": event.get("source_count", len(event.get("sources", []))),
        "confidence": event.get("confidence", "medium"),
        "claim_trace": event.get("claim_trace", []),
        "tw_highlight": event.get("tw_highlight", False),
        "selection_score": event.get("selection_score", 0),
    }

    # Conditional fields
    if event.get("sub_beat"):
        item["sub_beat"] = event["sub_beat"]
    if event.get("tw_highlight"):
        item["tw_highlight_reason"] = event.get("tw_highlight_reason", "")
    if event.get("single_source_warning"):
        item["single_source_warning"] = True
    elif item["source_count"] == 1:
        item["single_source_warning"] = True
    if event.get("opinion_level"):
        item["opinion_level"] = event["opinion_level"]
    if event.get("selection_reason") is not None:
        item["selection_reason"] = event["selection_reason"]

    return item


# ---------------------------------------------------------------------------
# Report JSON builder
# ---------------------------------------------------------------------------

def build_report(
    date_str: str,
    items: list[dict],
    dropped: list[dict],
    warnings: list[dict],
    stats: dict,
    beat_meta: dict[str, dict],
) -> dict:
    """組裝 report.schema.json 格式的主報告 JSON。

    Args:
        date_str: YYYY-MM-DD
        items: list of platform_output items
        dropped: list of dropped events（含 event_id, headline, selection_score, drop_reason）
        warnings: pipeline warnings
        stats: pipeline stats dict
        beat_meta: {beat_id: {name, emoji}}
    """
    date_compact = date_str.replace("-", "")
    now = datetime.now(TAIPEI)

    # Group items by beat
    sections = []
    items_by_beat: dict[str, list[dict]] = {}
    for item in items:
        beat = item.get("beat", "INTL")
        items_by_beat.setdefault(beat, []).append(item)

    for beat in BEAT_ORDER:
        beat_items = items_by_beat.get(beat, [])
        if not beat_items:
            continue
        meta = beat_meta.get(beat, BEAT_FALLBACK.get(beat, {"name": beat, "emoji": ""}))
        sections.append({
            "beat": beat,
            "title": meta["name"],
            "emoji": meta["emoji"],
            "items": beat_items,
        })

    # Handle unknown beats
    for beat, beat_items in items_by_beat.items():
        if beat not in BEAT_ORDER:
            meta = beat_meta.get(beat, {"name": beat, "emoji": ""})
            sections.append({
                "beat": beat,
                "title": meta["name"],
                "emoji": meta["emoji"],
                "items": beat_items,
            })

    # Determine status
    if not sections:
        status = "failed"
    elif len(warnings) > 0:
        status = "partial"
    else:
        status = "ok"

    report = {
        "reportId": f"daily_{date_compact}",
        "date": date_str,
        "timezone": "Asia/Taipei",
        "generated_at": now.isoformat(),
        "status": status,
        "warnings": _format_warnings(warnings),
        "sections": sections,
        "stats": _normalize_stats(stats),
    }

    if dropped:
        report["dropped_events"] = [
            {
                "event_id": d.get("event_id", ""),
                "headline": d.get("headline", ""),
                "selection_score": d.get("selection_score", 0),
                "drop_reason": d.get("drop_reason", "unknown"),
            }
            for d in dropped
        ]

    return report


def _format_warnings(warnings: list[dict]) -> list[dict]:
    """把 pipeline warnings 轉成 report.schema.json 的 warning 格式。"""
    valid_types = {"source_failed", "tier1_partial_failed", "section_empty",
                   "lint_warning", "other"}
    formatted = []
    for w in warnings:
        wtype = w.get("type", "other")
        if wtype not in valid_types:
            wtype = "lint_warning" if "lint" in wtype else "other"
        entry: dict = {
            "type": wtype,
            "message": w.get("message", str(w)),
        }
        if w.get("source_id"):
            entry["source_id"] = w["source_id"]
        formatted.append(entry)
    return formatted


def _normalize_stats(stats: dict) -> dict:
    """確保 stats 包含 report.schema.json 要求的所有欄位。"""
    required = [
        "total_feeds_checked", "total_feeds_failed",
        "total_articles_fetched", "total_articles_after_filter",
        "total_events_merged", "total_events_selected",
        "tw_highlights_count",
    ]
    normalized = {}
    for key in required:
        normalized[key] = stats.get(key, 0)
    return normalized


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------

def format_markdown(report: dict, beat_meta: dict[str, dict]) -> str:
    """產生 Markdown 可讀版。"""
    date_str = report.get("date", "")
    date_compact = date_str.replace("-", "")
    lines: list[str] = []

    # Header
    lines.append(f"# 阿卡夏圖書館・每日館報 {date_str}")
    lines.append("")
    lines.append(f"> Report ID: `daily_{date_compact}`")
    lines.append(f"> Generated: {report.get('generated_at', '')}")
    lines.append(f"> Status: {report.get('status', '')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Sections
    for section in report.get("sections", []):
        beat = section.get("beat", "")
        emoji = section.get("emoji", "")
        title = section.get("title", beat)
        lines.append(f"## {emoji} {title}")
        lines.append("")

        for item in section.get("items", []):
            headline = item.get("headline", "")
            context = item.get("context", "")
            confidence = item.get("confidence", "")
            sources = item.get("sources", [])
            tw = item.get("tw_highlight", False)

            # Headline
            tw_mark = " 🇹🇼" if tw else ""
            lines.append(f"### {headline}{tw_mark}")
            lines.append("")

            # Context
            if context:
                lines.append(context)
                lines.append("")

            # Metadata
            conf_label = {"high": "🟢 高", "medium": "🟡 中", "low": "🔴 低"}.get(
                confidence, confidence)
            src_count = item.get("source_count", len(sources))
            lines.append(f"*可信度: {conf_label} | 來源: {src_count}*")
            lines.append("")

            # Sources
            if sources:
                lines.append("<details><summary>來源</summary>")
                lines.append("")
                for s in sources:
                    pub = s.get("publisher", "")
                    title_s = s.get("title", "")
                    url = s.get("url", "")
                    if url:
                        lines.append(f"- [{pub}: {title_s}]({url})")
                    else:
                        lines.append(f"- {pub}: {title_s}")
                lines.append("")
                lines.append("</details>")
                lines.append("")

    # Stats
    stats = report.get("stats", {})
    lines.append("---")
    lines.append("")
    lines.append("## 📊 統計")
    lines.append("")
    lines.append(f"| 指標 | 數值 |")
    lines.append(f"|---|---|")
    lines.append(f"| 檢查來源 | {stats.get('total_feeds_checked', 0)} |")
    lines.append(f"| 失敗來源 | {stats.get('total_feeds_failed', 0)} |")
    lines.append(f"| 抓取文章 | {stats.get('total_articles_fetched', 0)} |")
    lines.append(f"| 過濾後文章 | {stats.get('total_articles_after_filter', 0)} |")
    lines.append(f"| 合併事件 | {stats.get('total_events_merged', 0)} |")
    lines.append(f"| 選入事件 | {stats.get('total_events_selected', 0)} |")
    lines.append(f"| 台灣相關 | {stats.get('tw_highlights_count', 0)} |")
    lines.append("")

    # Warnings
    warnings = report.get("warnings", [])
    if warnings:
        lines.append("## ⚠️ Warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- [{w.get('type', '')}] {w.get('message', '')}")
        lines.append("")

    # 參考來源彙整（所有連結集中底部，方便轉貼留言區）
    all_sources = _collect_all_sources(report)
    if all_sources:
        lines.append("---")
        lines.append("")
        lines.append("## 📎 參考來源")
        lines.append("")
        for s in all_sources:
            pub = s.get("publisher", "")
            title = s.get("title", "")
            url = s.get("url", "")
            if url:
                lines.append(f"- [{pub}: {title}]({url})")
            else:
                lines.append(f"- {pub}: {title}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Voice script
# ---------------------------------------------------------------------------

def format_voice_script(
    report: dict,
    date_str: str,
    beat_meta: dict[str, dict],
) -> str:
    """產生朗讀稿（規格 §12.3 + §13.3 + §13.4 + §13.5）。

    朗讀稿獨立生成，不是拿 X 版刪 emoji。
    """
    # 解析日期
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        year = dt.year
        month = dt.month
        day = dt.day
        weekday = WEEKDAY_ZH[dt.weekday()]
    except ValueError:
        year, month, day, weekday = 2026, 1, 1, "星期一"

    lines: list[str] = []

    # 開場（規格 §13.3）——「讓圖書館員翻譯給你聽」只在此出現一次
    lines.append("早安，這裡是阿卡夏圖書館。")
    lines.append(f"今天是 {year} 年 {month} 月 {day} 日，{weekday}。")
    lines.append("以下是今日的紀錄檔案，讓圖書館員翻譯給你聽。")
    lines.append("")

    # 各 beat 區塊
    for section in report.get("sections", []):
        beat = section.get("beat", "")
        items = section.get("items", [])
        if not items:
            continue

        # 區塊轉場語（規格 §13.4）
        transition = BEAT_TRANSITIONS.get(beat, "")
        if transition:
            lines.append(transition)
            lines.append("")

        for item in items:
            voice_text = item.get("voice_text", "")
            if voice_text:
                lines.append(voice_text)
                lines.append("")
                # 來源宣告已包含在 Claude 產出的 voice_text 中（規格 §13.5）。
                # 不再由 formatter 額外追加，避免重複朗讀來源資訊。

    # 結語
    lines.append("以上是今天的館報。")
    lines.append("我們明天見。")

    # 參考來源彙整（所有來源連結集中底部，方便貼社群留言）
    all_sources = _collect_all_sources(report)
    if all_sources:
        lines.append("")
        lines.append("---")
        lines.append("參考來源：")
        for s in all_sources:
            pub = s.get("publisher", "")
            title = s.get("title", "")
            url = s.get("url", "")
            if url:
                lines.append(f"- {pub}: {title}")
                lines.append(f"  {url}")
            else:
                lines.append(f"- {pub}: {title}")

    return "\n".join(lines)


def _collect_all_sources(report: dict) -> list[dict]:
    """收集 report 中所有不重複的 source（用 url 去重，保留順序）。"""
    seen_urls: set[str] = set()
    result: list[dict] = []
    for section in report.get("sections", []):
        for item in section.get("items", []):
            for s in item.get("sources", []):
                url = s.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    result.append(s)
    return result


def _build_source_attribution(sources: list[dict], date_str: str) -> str:
    """產生來源宣告（規格 §13.5）。"""
    if not sources:
        return ""

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        date_zh = f"{dt.year} 年 {dt.month} 月 {dt.day} 日"
    except ValueError:
        date_zh = date_str

    publishers = []
    for s in sources:
        pub = s.get("publisher", "")
        if pub and pub not in publishers:
            publishers.append(pub)

    if len(publishers) == 1:
        return f"本館報來自 {publishers[0]} 新聞，於 {date_zh} 發佈，讓圖書館員翻譯給你聽。"
    elif len(publishers) >= 2:
        last = publishers[-1]
        rest = "、".join(publishers[:-1])
        return f"本則整理自 {rest} 與 {last} 於 {date_zh} 發佈的報導。"
    return ""


# ---------------------------------------------------------------------------
# X / Threads platform draft
# ---------------------------------------------------------------------------

def format_x_draft(report: dict) -> dict:
    """產生 X 貼文草稿 JSON。"""
    date_str = report.get("date", "")
    date_compact = date_str.replace("-", "")

    draft = {
        "reportId": f"daily_{date_compact}",
        "date": date_str,
        "platform": "x",
        "max_chars_per_post": X_MAX_CHARS,
        "events": [],
    }

    for section in report.get("sections", []):
        for item in section.get("items", []):
            draft["events"].append({
                "event_id": item.get("event_id", ""),
                "beat": item.get("beat", ""),
                "headline": item.get("headline", ""),
                "posts": item.get("platform_outputs", {}).get("x", {}).get("posts", []),
            })

    return draft


def format_threads_draft(report: dict) -> dict:
    """產生 Threads 貼文草稿 JSON。"""
    date_str = report.get("date", "")
    date_compact = date_str.replace("-", "")

    draft = {
        "reportId": f"daily_{date_compact}",
        "date": date_str,
        "platform": "threads",
        "max_chars_per_post": THREADS_MAX_CHARS,
        "events": [],
    }

    for section in report.get("sections", []):
        for item in section.get("items", []):
            draft["events"].append({
                "event_id": item.get("event_id", ""),
                "beat": item.get("beat", ""),
                "headline": item.get("headline", ""),
                "posts": item.get("platform_outputs", {}).get("threads", {}).get("posts", []),
            })

    return draft


# ---------------------------------------------------------------------------
# Run log
# ---------------------------------------------------------------------------

def build_run_log(
    date_str: str,
    steps: list[dict],
    warnings: list[dict],
    stats: dict,
    start_time: float,
    status: str = "ok",
) -> dict:
    """產生 run log JSON。"""
    date_compact = date_str.replace("-", "")
    end_time = time.time()

    return {
        "reportId": f"daily_{date_compact}",
        "date": date_str,
        "timezone": "Asia/Taipei",
        "generated_at": datetime.now(TAIPEI).isoformat(),
        "status": status,
        "duration_seconds": round(end_time - start_time, 2),
        "steps": steps,
        "warnings_count": len(warnings),
        "warnings": _format_warnings(warnings),
        "stats": _normalize_stats(stats),
    }


# ---------------------------------------------------------------------------
# Output validation
# ---------------------------------------------------------------------------

def validate_report_output(report: dict) -> list[dict]:
    """驗證 report 的 P0 驗收條件。

    不依賴 jsonschema 套件——手動檢查 ROADMAP Phase 4 的驗收項目：
    1. voice_text 不含 URL / emoji / N/N / Markdown link
    2. X 每則 ≤ 280 字
    3. Threads 每則 ≤ 500 字
    4. 每個 section 有 items
    """
    from src.validators import VOICE_FORBIDDEN_PATTERNS

    issues: list[dict] = []

    for section in report.get("sections", []):
        for item in section.get("items", []):
            eid = item.get("event_id", "?")

            # voice_text lint
            vt = item.get("voice_text", "")
            for pattern, desc in VOICE_FORBIDDEN_PATTERNS:
                if pattern.search(vt):
                    issues.append({
                        "type": "lint_warning",
                        "message": f"{eid}: voice_text {desc}",
                    })

            # X post length
            x_posts = item.get("platform_outputs", {}).get("x", {}).get("posts", [])
            for i, post in enumerate(x_posts):
                if len(post) > X_MAX_CHARS:
                    issues.append({
                        "type": "lint_warning",
                        "message": f"{eid}: X post[{i}] 長度 {len(post)} > {X_MAX_CHARS}",
                    })

            # Threads post length
            t_posts = item.get("platform_outputs", {}).get("threads", {}).get("posts", [])
            for i, post in enumerate(t_posts):
                if len(post) > THREADS_MAX_CHARS:
                    issues.append({
                        "type": "lint_warning",
                        "message": f"{eid}: Threads post[{i}] 長度 {len(post)} > {THREADS_MAX_CHARS}",
                    })

            # Required fields check
            for field in ("headline", "confidence", "claim_trace"):
                if not item.get(field):
                    issues.append({
                        "type": "lint_warning",
                        "message": f"{eid}: 缺少必要欄位 {field}",
                    })

            # source_count = 1 → single_source_warning
            if item.get("source_count", 0) == 1 and not item.get("single_source_warning"):
                issues.append({
                    "type": "lint_warning",
                    "message": f"{eid}: source_count=1 但缺少 single_source_warning",
                })

    return issues


# ---------------------------------------------------------------------------
# Full output pipeline
# ---------------------------------------------------------------------------

def generate_all_outputs(
    date_str: str,
    rewritten_events: list[dict],
    dropped_events: list[dict],
    pipeline_warnings: list[dict],
    pipeline_stats: dict,
    steps: list[dict] | None = None,
    start_time: float | None = None,
    output_base: Path = OUTPUT_BASE,
    dry_run: bool = False,
) -> tuple[dict, list[dict]]:
    """產出所有六種輸出檔。

    Args:
        date_str: YYYY-MM-DD
        rewritten_events: 改寫後的 events（已含 headline, voice_text 等）
        dropped_events: 被 drop 的 events
        pipeline_warnings: 累計 warnings
        pipeline_stats: pipeline 統計
        steps: run log 步驟紀錄
        start_time: pipeline 啟動時間
        output_base: 輸出目錄根
        dry_run: True 時不寫檔，只回傳 report

    Returns:
        (report_dict, validation_issues)
    """
    date_compact = date_str.replace("-", "")
    _start = start_time or time.time()

    # Load beat metadata
    beat_meta = load_beat_meta()

    # 1. Build platform_output items
    items = [build_platform_output_item(e) for e in rewritten_events]
    LOG.info("Built %d platform_output items", len(items))

    # 2. Build report JSON
    report = build_report(
        date_str, items, dropped_events, pipeline_warnings, pipeline_stats, beat_meta,
    )

    # 3. Validate
    validation_issues = validate_report_output(report)
    if validation_issues:
        LOG.warning("Validation issues: %d", len(validation_issues))
        for issue in validation_issues:
            LOG.warning("  %s", issue.get("message", ""))
        # Add to report warnings
        report["warnings"].extend(_format_warnings(validation_issues))
        if report["status"] == "ok":
            report["status"] = "partial"

    # 4. Generate other formats
    markdown = format_markdown(report, beat_meta)
    voice = format_voice_script(report, date_str, beat_meta)
    x_draft = format_x_draft(report)
    threads_draft = format_threads_draft(report)
    run_log = build_run_log(
        date_str,
        steps or [],
        pipeline_warnings + validation_issues,
        pipeline_stats,
        _start,
        status=report["status"],
    )

    if dry_run:
        LOG.info("[DRY-RUN] 跳過寫檔")
        return report, validation_issues

    # 5. Write files
    _ensure_dirs(output_base)

    # daily_YYYYMMDD.json
    json_path = output_base / f"daily_{date_compact}.json"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    LOG.info("Written: %s", json_path)

    # daily_YYYYMMDD.md
    md_path = output_base / f"daily_{date_compact}.md"
    md_path.write_text(markdown, encoding="utf-8")
    LOG.info("Written: %s", md_path)

    # voice_YYYYMMDD.txt
    voice_path = output_base / f"voice_{date_compact}.txt"
    voice_path.write_text(voice, encoding="utf-8")
    LOG.info("Written: %s", voice_path)

    # platforms/x_YYYYMMDD.json
    x_path = output_base / "platforms" / f"x_{date_compact}.json"
    x_path.write_text(
        json.dumps(x_draft, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    LOG.info("Written: %s", x_path)

    # platforms/threads_YYYYMMDD.json
    threads_path = output_base / "platforms" / f"threads_{date_compact}.json"
    threads_path.write_text(
        json.dumps(threads_draft, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    LOG.info("Written: %s", threads_path)

    # logs/run_YYYYMMDD.json
    log_path = output_base / "logs" / f"run_{date_compact}.json"
    log_path.write_text(
        json.dumps(run_log, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    LOG.info("Written: %s", log_path)

    return report, validation_issues


def _ensure_dirs(output_base: Path) -> None:
    """確保輸出目錄結構存在。"""
    output_base.mkdir(parents=True, exist_ok=True)
    (output_base / "platforms").mkdir(exist_ok=True)
    (output_base / "logs").mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate all output formats from rewritten events.")
    parser.add_argument("--events-base", type=Path, default=DEFAULT_EVENTS_BASE)
    parser.add_argument("--output-base", type=Path, default=OUTPUT_BASE)
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true",
                        help="不寫檔，只驗證格式")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    date = args.date or datetime.now(TAIPEI).strftime("%Y-%m-%d")
    events_dir = args.events_base / date

    if not events_dir.exists():
        LOG.error("Events directory not found: %s", events_dir)
        return 1

    # 讀 selection manifest
    manifest_path = events_dir / "_selection_manifest.json"
    if not manifest_path.exists():
        LOG.error("Selection manifest not found: %s", manifest_path)
        LOG.error("請先跑完 Phase 1-3 pipeline")
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected_ids = set(manifest.get("selected_event_ids", []))

    # 讀 selected events（改寫後）
    events = []
    for eid in selected_ids:
        fp = events_dir / f"{eid}.json"
        if fp.exists():
            events.append(json.loads(fp.read_text(encoding="utf-8")))
        else:
            LOG.warning("Event file not found: %s", fp)

    # 讀 dropped events
    dropped = manifest.get("dropped", [])

    # 讀 rewrite log 的 warnings
    rewrite_log_path = events_dir / "_rewrite_log.json"
    rewrite_warnings: list[dict] = []
    if rewrite_log_path.exists():
        rlog = json.loads(rewrite_log_path.read_text(encoding="utf-8"))
        rewrite_warnings = rlog.get("lint_warnings", [])

    # Pipeline stats（MVP: 從已有數據推算）
    stats = {
        "total_feeds_checked": 26,  # from feeds.yaml enabled count
        "total_feeds_failed": 0,
        "total_articles_fetched": 0,
        "total_articles_after_filter": 0,
        "total_events_merged": len(selected_ids) + len(dropped),
        "total_events_selected": len(selected_ids),
        "tw_highlights_count": sum(1 for e in events if e.get("tw_highlight")),
    }

    LOG.info("Formatting %d selected events (+ %d dropped)", len(events), len(dropped))

    start = time.time()
    report, issues = generate_all_outputs(
        date_str=date,
        rewritten_events=events,
        dropped_events=dropped,
        pipeline_warnings=rewrite_warnings,
        pipeline_stats=stats,
        output_base=args.output_base,
        dry_run=args.dry_run,
        start_time=start,
    )

    LOG.info("Done. Status: %s, validation issues: %d", report.get("status"), len(issues))
    return 0


if __name__ == "__main__":
    sys.exit(main())
