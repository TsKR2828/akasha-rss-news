"""媒體（outlet）歸戶：把同一家媒體的多個 feed 頻道算成一家。

2026-09-26 改善研究 S0-2：selector 的「多來源 +30」、confidence=high、
single_source_warning 原本都看「不同 source_id 數」，路透兩個 Google News
頻道、衛報八個頻道各算一個來源，於是同一家媒體的兩篇報導被標成
「多方確認・可信度高」（30 天 48 則，其中 30 則標 high）。

歸戶規則：source_id 第一個底線前的字首就是媒體名
（guardian_books → guardian、reuters_world_google_news → reuters），
少數字首不代表媒體的 id 用 _OVERRIDES 指定。
"""
from __future__ import annotations

from typing import Iterable

# 字首規則不適用的 source_id（例：the_verge 字首是 "the"）
_OVERRIDES: dict[str, str] = {
    "the_verge": "the_verge",
}


def outlet_of(source_id: str) -> str:
    """回傳 source_id 所屬的媒體代號。"""
    if not source_id:
        return ""
    if source_id in _OVERRIDES:
        return _OVERRIDES[source_id]
    return source_id.split("_", 1)[0]


def distinct_outlets(sources: Iterable[dict]) -> set[str]:
    """一則事件的來源清單中，不同媒體的集合。"""
    return {outlet_of(s.get("source_id", "")) for s in sources if s.get("source_id")}


def outlet_count(sources: Iterable[dict]) -> int:
    return len(distinct_outlets(sources))
