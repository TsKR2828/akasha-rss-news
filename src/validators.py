"""Phase 3 — Content validators (banned_phrases, voice_text lint, confidence).

對應規格：
- §13 文風禁用詞（from config/style_guide.md）
- §12.3 / §17.2 voice_text 不得含 URL、emoji 🧵📌📎、1/N、Markdown link
- §9.2 confidence 三級分類驗證
- §9.3 claim_trace 每條 claim 對應 source_id

用法：
    from src.validators import lint_rewrite_output
    warnings = lint_rewrite_output(rewrite_result, event_sources)
"""
from __future__ import annotations

import re
from typing import Optional


# --- 禁用詞（規格 §13，同 config/style_guide.md）---

BANNED_PHRASES = [
    "據悉",
    "有鑑於此",
    "引發關注",
    "受到矚目",
    "備受矚目",
    "值得一提的是",
    "不容忽視",
    "相關單位表示",
]

# --- voice_text 禁止 pattern（規格 §17.2）---

VOICE_FORBIDDEN_PATTERNS = [
    (re.compile(r"https?://"), "contains URL"),
    (re.compile(r"🧵"), "contains 🧵 emoji"),
    (re.compile(r"📌"), "contains 📌 emoji"),
    (re.compile(r"📎"), "contains 📎 emoji"),
    (re.compile(r"(?:^|\s)\d{1,2}/\d{1,2}(?=\s|$)"), "contains N/N numbering"),
    (re.compile(r"\[[^\]]+\]\([^)]+\)"), "contains Markdown link"),
    # FIX-B (0706 健檢): 零來源規則明文禁止的 per-event 來源標注句型，
    # 例如「這則消息目前只有一個來源」「本則整理自 XX 的報導」等。
    # 舊 pattern 只擋 URL/emoji/編號/Markdown link，擋不住這類中文敘述句。
    (re.compile(r"只有(?:一|1|兩|2|\d+)個?來源"), "contains per-event source-count phrase"),
    (re.compile(r"只有.{0,6}一個來源"), "contains per-event source-count phrase"),
    (re.compile(r"只(?:來自|來源自)"), "contains single-source attribution phrase"),
    (re.compile(r"目前(?:的)?來源(?:提供的細節)?"), "contains source-attribution phrase"),
    (re.compile(r"本則(?:整理自|來自)"), "contains per-event source attribution phrase"),
    (re.compile(r"本館報來自"), "contains per-event source attribution phrase"),
    (re.compile(r"根據.{0,10}報導"), "contains per-event source attribution phrase"),
    (re.compile(r".{0,10}報導指出"), "contains per-event source attribution phrase"),
]


# --- Lint functions ---

def validate_banned_phrases(text: str) -> list[dict]:
    """檢查文字中是否出現禁用詞。

    Returns:
        list of {type: "banned_phrase", phrase: str, message: str}
    """
    if not text:
        return []
    warnings = []
    for phrase in BANNED_PHRASES:
        if phrase in text:
            warnings.append({
                "type": "banned_phrase",
                "phrase": phrase,
                "message": f"禁用詞「{phrase}」出現在文字中",
            })
    return warnings


def validate_voice_text(voice_text: str) -> list[dict]:
    """檢查 voice_text 是否符合規格 §17.2。

    Returns:
        list of {type: "voice_text_lint", pattern: str, message: str}
    """
    if not voice_text:
        return [{"type": "voice_text_lint", "pattern": "empty", "message": "voice_text 為空"}]
    warnings = []
    for pattern, desc in VOICE_FORBIDDEN_PATTERNS:
        if pattern.search(voice_text):
            warnings.append({
                "type": "voice_text_lint",
                "pattern": desc,
                "message": f"voice_text {desc}",
            })
    return warnings


def validate_confidence(
    confidence: str,
    sources: list[dict],
    source_tiers: Optional[list] = None,
) -> dict | None:
    """檢查 confidence 是否合理（規格 §9.2）。

    不強制覆寫（Claude 可能有更好的判斷），但回傳 warning 如果不一致。

    Returns:
        warning dict or None
    """
    if confidence not in ("high", "medium", "low"):
        return {
            "type": "confidence_invalid",
            "message": f"confidence 值 '{confidence}' 不在 high/medium/low 之中",
        }

    source_count = len(sources) if sources else 0
    tiers = source_tiers or []

    # 推斷預期 confidence
    high_tier_count = sum(1 for t in tiers if t in (1, 2))
    distinct_sources = {s.get("source_id") for s in sources} if sources else set()

    if len(distinct_sources) >= 2 and high_tier_count >= 2:
        expected = "high"
    else:
        expected = "medium"

    if confidence != expected:
        return {
            "type": "confidence_mismatch",
            "expected": expected,
            "actual": confidence,
            "message": f"confidence 為 '{confidence}'，但依來源推斷應為 '{expected}'",
        }
    return None


def validate_claim_trace(
    claim_trace: list[dict],
    sources: list[dict],
) -> list[dict]:
    """驗證 claim_trace 中每條 claim 都對應到 sources 中的 source_id。

    Returns:
        list of error dicts
    """
    if not claim_trace:
        return [{
            "type": "claim_trace_empty",
            "message": "claim_trace 為空，規格要求至少 1 條",
        }]

    source_ids = {s.get("source_id") for s in sources} if sources else set()
    errors = []

    for i, ct in enumerate(claim_trace):
        claim_text = ct.get("claim", "")
        sid = ct.get("source_id", "")
        support = ct.get("support_type", "")

        if not claim_text or not claim_text.strip():
            errors.append({
                "type": "claim_empty",
                "index": i,
                "message": f"claim_trace[{i}] 的 claim 文字為空",
            })

        if not sid:
            errors.append({
                "type": "claim_no_source_id",
                "index": i,
                "message": f"claim_trace[{i}] 缺少 source_id",
            })
        elif sid not in source_ids:
            errors.append({
                "type": "claim_source_not_found",
                "index": i,
                "source_id": sid,
                "message": f"claim_trace[{i}] 的 source_id '{sid}' 不在 sources 中",
            })

        if support not in ("direct", "indirect", "background"):
            errors.append({
                "type": "claim_invalid_support_type",
                "index": i,
                "support_type": support,
                "message": f"claim_trace[{i}] 的 support_type '{support}' 無效",
            })

    return errors


def validate_opinion_level(opinion_level: str) -> dict | None:
    """檢查 opinion_level 是否為合法值。"""
    valid = ("none", "light_context", "explicit_commentary")
    if opinion_level not in valid:
        return {
            "type": "opinion_level_invalid",
            "message": f"opinion_level '{opinion_level}' 不在 {valid} 之中",
        }
    return None


def validate_platform_lengths(
    thread_text: str,
    threads_text: str,
    x_max: int = 280,
    threads_max: int = 500,
) -> list[dict]:
    """檢查平台文字長度（整段，切分在 formatter 做）。"""
    warnings = []
    # 只警告單則超長；thread_text 可能包含多則，整段超 280 是正常的
    # 這裡只做基本 sanity check
    if thread_text and len(thread_text) > x_max * 10:
        warnings.append({
            "type": "thread_text_too_long",
            "length": len(thread_text),
            "message": f"thread_text 長度 {len(thread_text)} 超過合理範圍",
        })
    if threads_text and len(threads_text) > threads_max * 5:
        warnings.append({
            "type": "threads_text_too_long",
            "length": len(threads_text),
            "message": f"threads_text 長度 {len(threads_text)} 超過合理範圍",
        })
    return warnings


# --- 整合 lint ---

def lint_rewrite_output(
    rewrite: dict,
    event_sources: list[dict],
    source_tiers: Optional[list] = None,
) -> list[dict]:
    """對 Claude 改寫結果跑完整 lint，回傳所有 warnings / errors。

    Args:
        rewrite: Claude 回傳的 JSON（headline, context, voice_text, ...）
        event_sources: 原始 event 的 sources list
        source_tiers: 原始 event 的 source_tiers list

    Returns:
        list of warning/error dicts，每個含 type + message
    """
    issues: list[dict] = []

    # 1. 禁用詞：檢查所有文字欄位
    for field in ("headline", "context", "thread_text", "threads_text", "voice_text"):
        text = rewrite.get(field, "")
        if text:
            for w in validate_banned_phrases(text):
                w["field"] = field
                issues.append(w)

    # 2. voice_text lint
    issues.extend(validate_voice_text(rewrite.get("voice_text", "")))

    # 3. confidence
    conf_warning = validate_confidence(
        rewrite.get("confidence", ""),
        event_sources,
        source_tiers,
    )
    if conf_warning:
        issues.append(conf_warning)

    # 4. opinion_level
    op_warning = validate_opinion_level(rewrite.get("opinion_level", ""))
    if op_warning:
        issues.append(op_warning)

    # 5. claim_trace
    issues.extend(validate_claim_trace(
        rewrite.get("claim_trace", []),
        event_sources,
    ))

    # 6. platform lengths
    issues.extend(validate_platform_lengths(
        rewrite.get("thread_text", ""),
        rewrite.get("threads_text", ""),
    ))

    return issues
