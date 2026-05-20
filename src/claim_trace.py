"""Phase 3 — Claim trace verification.

驗證 Claude 改寫產出的 claim_trace 是否合法：
- 每個 claim 對應到 event.sources 裡的 source_id
- source_url 與 sources 中的 url 一致
- support_type 合法（direct / indirect / background）
- source_count = 1 時加入 single_source_warning

對應規格：
- §9.3 claim_trace 規則
- §20.1 P0: 每個 selected item 至少 1 條 claim_trace

用法：
    from src.claim_trace import verify_and_fix_claim_trace
    fixed, issues = verify_and_fix_claim_trace(claim_trace, event)
"""
from __future__ import annotations


def verify_claim_trace(
    claim_trace: list[dict],
    sources: list[dict],
) -> list[dict]:
    """驗證 claim_trace 合法性。

    Args:
        claim_trace: Claude 產出的 claim_trace list
        sources: event 的 sources list（ground truth）

    Returns:
        list of issue dicts: {type, index, message, ...}
    """
    issues: list[dict] = []

    if not claim_trace:
        issues.append({
            "type": "no_claims",
            "message": "claim_trace 為空，規格 §9.3 要求至少 1 條",
        })
        return issues

    source_map = {s["source_id"]: s for s in sources}

    for i, ct in enumerate(claim_trace):
        # 必填欄位
        if not ct.get("claim"):
            issues.append({
                "type": "empty_claim",
                "index": i,
                "message": f"claim_trace[{i}] claim 為空",
            })

        sid = ct.get("source_id", "")
        if not sid:
            issues.append({
                "type": "missing_source_id",
                "index": i,
                "message": f"claim_trace[{i}] 缺少 source_id",
            })
        elif sid not in source_map:
            issues.append({
                "type": "unknown_source_id",
                "index": i,
                "source_id": sid,
                "available": list(source_map.keys()),
                "message": f"claim_trace[{i}] 的 source_id '{sid}' 不在 event sources 中",
            })

        # support_type
        stype = ct.get("support_type", "")
        if stype not in ("direct", "indirect", "background"):
            issues.append({
                "type": "invalid_support_type",
                "index": i,
                "support_type": stype,
                "message": f"claim_trace[{i}] support_type '{stype}' 無效",
            })

    return issues


def fix_claim_trace(
    claim_trace: list[dict],
    sources: list[dict],
) -> list[dict]:
    """修正 claim_trace 中可自動修正的問題。

    修正邏輯：
    - source_url 不一致 → 用 sources 中的 url 覆蓋
    - source_title 缺失 → 用 sources 中的 title 補上
    - source_id 無效的 claim → 移除（記 warning）
    - support_type 無效 → 預設 "direct"

    Args:
        claim_trace: 原始 claim_trace
        sources: event 的 sources

    Returns:
        fixed claim_trace（新 list，不改原物件）
    """
    source_map = {s["source_id"]: s for s in sources}
    fixed = []

    for ct in claim_trace:
        sid = ct.get("source_id", "")
        if not sid or sid not in source_map:
            # 無法修正的 claim → 跳過
            continue

        src = source_map[sid]
        new_ct = dict(ct)

        # 補齊 / 修正 source_url
        new_ct["source_url"] = src.get("url", ct.get("source_url", ""))

        # 補齊 source_title
        if not new_ct.get("source_title"):
            new_ct["source_title"] = src.get("title", "")

        # 修正 support_type
        if new_ct.get("support_type") not in ("direct", "indirect", "background"):
            new_ct["support_type"] = "direct"

        fixed.append(new_ct)

    return fixed


def verify_and_fix_claim_trace(
    claim_trace: list[dict],
    event: dict,
) -> tuple[list[dict], list[dict]]:
    """驗證 + 修正 claim_trace。

    Args:
        claim_trace: Claude 改寫產出的 claim_trace
        event: 完整 event dict（含 sources）

    Returns:
        (fixed_claim_trace, issues)
    """
    sources = event.get("sources", [])

    # 1. 驗證
    issues = verify_claim_trace(claim_trace, sources)

    # 2. 修正
    fixed = fix_claim_trace(claim_trace, sources)

    # 3. 如果修正後為空，用 event 的第一個 source 建立 fallback claim
    if not fixed and sources:
        first = sources[0]
        fixed = [{
            "claim": event.get("headline", "事件摘要"),
            "source_id": first["source_id"],
            "source_title": first.get("title", ""),
            "source_url": first.get("url", ""),
            "support_type": "direct",
        }]
        issues.append({
            "type": "fallback_claim_created",
            "message": "所有 claim 無效，已用第一個 source 建立 fallback claim",
        })

    return fixed, issues


def derive_single_source_warning(source_count: int) -> bool:
    """規格 §20.1 P0：source_count = 1 → single_source_warning = true。"""
    return source_count == 1
