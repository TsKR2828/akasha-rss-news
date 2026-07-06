"""Phase 3 — Claude rewrite: selected events → 改寫後的館報 items.

把 Phase 2 選出的 events 送給 Claude，產出：
- headline（繁中事件標題）
- context（脈絡說明）
- thread_text（X 版）
- threads_text（Threads 版）
- voice_text（朗讀版）
- confidence / opinion_level
- claim_trace（事實回溯）

對應規格：
- §9  事實安全
- §10 Prompt Injection 防護
- §12 voice_text 格式
- §13 文風
- §17 platform_output

CLI 用法：
    python -m src.claude_rewrite --date 2026-05-19
    python -m src.claude_rewrite --date 2026-05-19 --dry-run
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

from src.html_cleaner import clean_html, strip_tracking_params
from src.claim_trace import verify_and_fix_claim_trace, derive_single_source_warning
from src.validators import lint_rewrite_output

LOG = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVENTS_BASE = PROJECT_ROOT / "data" / "events"
PROMPT_PATH = PROJECT_ROOT / "prompts" / "rewrite_prompt.md"

TAIPEI = timezone(timedelta(hours=8))

# Claude API 設定
# 注意：雲端 Routine 的改寫由 claude.ai Routine session 模型執行（見
# prompts/routine_prompt.md Step 2 鐵則），不呼叫這支 API；此常數只影響
# 本地 / 直接呼叫 API 的路徑，改動不影響 production 的實際改寫模型。
MODEL = "claude-sonnet-5"
MAX_TOKENS = 4096
TEMPERATURE = 0.3  # 低溫度：改寫需忠於原文

# 重試設定
MAX_RETRIES = 2
RETRY_DELAY = 3  # 秒


def load_prompt() -> str:
    """載入 rewrite_prompt.md。"""
    return PROMPT_PATH.read_text(encoding="utf-8")


def _init_client():
    """Lazy-init Anthropic client。"""
    try:
        import anthropic
        return anthropic.Anthropic()
    except ImportError:
        LOG.error("anthropic 套件未安裝，請執行 pip install anthropic")
        raise
    except Exception as e:
        LOG.error("無法初始化 Anthropic client: %s", e)
        raise


def prepare_event_payload(event: dict) -> dict:
    """把 event 轉成 rewrite_prompt.md 定義的輸入格式。

    清理 HTML + 追蹤參數後再送出。
    """
    cleaned_sources = []
    for s in event.get("sources", []):
        cleaned_sources.append({
            "source_id": s.get("source_id", ""),
            "publisher": s.get("publisher", ""),
            "title": clean_html(s.get("title", "")),
            "summary": clean_html(s.get("summary", "") or ""),
            "url": strip_tracking_params(s.get("url", "")),
            "published_at": s.get("published_at", ""),
        })

    return {
        "event_id": event.get("event_id", ""),
        "beat": event.get("beat", ""),
        "sources": cleaned_sources,
        "tw_highlight": event.get("tw_highlight", False),
        "constraints": {
            "x_max_chars": 280,
            "threads_max_chars": 500,
        },
    }


def parse_claude_response(response_text: str) -> dict | None:
    """嘗試從 Claude 回應中解析 JSON。

    Claude 可能回傳 ```json ... ``` 或純 JSON。
    """
    text = response_text.strip()

    # 嘗試直接 parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 嘗試從 markdown code block 提取
    import re
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    LOG.warning("無法解析 Claude 回應為 JSON")
    return None


def call_claude(
    client,
    system_prompt: str,
    event_payload: dict,
    model: str = MODEL,
    max_tokens: int = MAX_TOKENS,
    temperature: float = TEMPERATURE,
) -> dict | None:
    """呼叫 Claude API 改寫一個 event。

    Returns:
        parsed JSON dict or None
    """
    user_message = json.dumps(event_payload, ensure_ascii=False, indent=2)

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            # 取得回應文字
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text

            result = parse_claude_response(response_text)
            if result is not None:
                return result

            LOG.warning("Attempt %d: Claude 回應無法解析為 JSON", attempt + 1)

        except Exception as e:
            LOG.warning("Attempt %d failed: %s", attempt + 1, e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (attempt + 1))

    return None


def merge_rewrite_into_event(event: dict, rewrite: dict) -> dict:
    """把 Claude 改寫結果合併回 event dict。

    只覆蓋改寫產出的欄位，保留 event 的結構性欄位
    （article_ids, sources, source_count, source_tiers, selection_score 等）。
    """
    merged = dict(event)

    # Claude 改寫的欄位
    rewrite_fields = [
        "headline", "context",
        "thread_text", "threads_text", "voice_text",
        "confidence", "opinion_level",
    ]
    for field in rewrite_fields:
        if field in rewrite:
            merged[field] = rewrite[field]

    # claim_trace: 驗證 + 修正後再合併
    if "claim_trace" in rewrite:
        fixed_ct, ct_issues = verify_and_fix_claim_trace(
            rewrite["claim_trace"], event,
        )
        merged["claim_trace"] = fixed_ct
        if ct_issues:
            LOG.info("  claim_trace 修正: %d issues", len(ct_issues))
            for issue in ct_issues:
                LOG.debug("    %s", issue.get("message", ""))

    # single_source_warning
    merged["single_source_warning"] = derive_single_source_warning(
        merged.get("source_count", 0),
    )

    return merged


def rewrite_event(
    event: dict,
    client,
    system_prompt: str,
    dry_run: bool = False,
    model: str = MODEL,
) -> tuple[dict, list[dict]]:
    """改寫單一 event。

    Args:
        event: 選入的 event dict
        client: Anthropic client（或 mock）
        system_prompt: 已載入的 rewrite prompt
        dry_run: True 時不呼叫 API，回傳原始 event
        model: Claude model 名稱

    Returns:
        (rewritten_event, lint_warnings)
    """
    event_id = event.get("event_id", "unknown")

    if dry_run:
        LOG.info("  [DRY-RUN] %s — 跳過 API 呼叫", event_id)
        return event, []

    # 1. 準備 payload
    payload = prepare_event_payload(event)

    # 2. 呼叫 Claude
    LOG.info("  calling Claude for %s (%s)...", event_id, event.get("beat", "?"))
    rewrite = call_claude(client, system_prompt, payload, model=model)

    if rewrite is None:
        LOG.error("  %s: Claude 改寫失敗，保留原始內容", event_id)
        return event, [{
            "type": "rewrite_failed",
            "event_id": event_id,
            "message": "Claude API 回傳無法解析，保留原始 event",
        }]

    # 3. Lint
    lint_issues = lint_rewrite_output(
        rewrite,
        event.get("sources", []),
        event.get("source_tiers"),
    )
    if lint_issues:
        LOG.info("  %s: %d lint issues", event_id, len(lint_issues))
        for issue in lint_issues:
            LOG.debug("    [%s] %s", issue.get("type", ""), issue.get("message", ""))

    # 4. 合併
    merged = merge_rewrite_into_event(event, rewrite)

    return merged, lint_issues


def rewrite_selected_events(
    events: list[dict],
    client=None,
    system_prompt: str | None = None,
    dry_run: bool = False,
    model_override: str | None = None,
) -> tuple[list[dict], list[dict]]:
    """改寫所有 selected events。

    Args:
        events: selected event list
        client: Anthropic client（None 時自動初始化）
        system_prompt: 改寫 prompt（None 時從檔案載入）
        dry_run: True 時不呼叫 API
        model_override: 覆蓋預設 model 名稱

    Returns:
        (rewritten_events, all_lint_warnings)
    """
    _model = model_override or MODEL

    if system_prompt is None:
        system_prompt = load_prompt()

    if client is None and not dry_run:
        client = _init_client()

    rewritten = []
    all_warnings: list[dict] = []

    for i, event in enumerate(events):
        LOG.info("[%d/%d] %s", i + 1, len(events), event.get("event_id", "?"))
        result, warnings = rewrite_event(
            event, client, system_prompt, dry_run, model=_model,
        )
        rewritten.append(result)
        all_warnings.extend(warnings)

    return rewritten, all_warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Rewrite selected events with Claude.")
    parser.add_argument("--events-base", type=Path, default=DEFAULT_EVENTS_BASE)
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true",
                        help="不呼叫 API，只驗證 pipeline 流程")
    parser.add_argument("--model", type=str, default=MODEL)
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
        LOG.error("請先跑 python -m src.selector --date %s", date)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected_ids = set(manifest.get("selected_event_ids", []))

    if not selected_ids:
        LOG.warning("沒有 selected events，跳過改寫")
        return 0

    # 讀 selected events
    events = []
    for eid in selected_ids:
        fp = events_dir / f"{eid}.json"
        if fp.exists():
            events.append(json.loads(fp.read_text(encoding="utf-8")))
        else:
            LOG.warning("Event file not found: %s", fp)

    LOG.info("Selected events: %d", len(events))

    # 改寫
    rewritten, warnings = rewrite_selected_events(
        events, dry_run=args.dry_run, model_override=args.model,
    )

    # 寫回
    if not args.dry_run:
        for evt in rewritten:
            fp = events_dir / f"{evt['event_id']}.json"
            fp.write_text(
                json.dumps(evt, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    # 寫 rewrite log
    log = {
        "date": date,
        "model": args.model,
        "dry_run": args.dry_run,
        "events_count": len(rewritten),
        "lint_warnings_count": len(warnings),
        "lint_warnings": warnings,
    }
    (events_dir / "_rewrite_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    LOG.info("Done. %d events rewritten, %d lint warnings.",
             len(rewritten), len(warnings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
