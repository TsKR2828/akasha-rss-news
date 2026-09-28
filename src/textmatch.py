"""關鍵字比對：英文整字、中文子字串。

2026-09-26 改善研究 SEL-7：分類與選題加分原本用「字裡面有就算」
（kw in text），於是 Staten Island／statements 命中 Tate、senator 命中 NATO、
Warren 命中 war、soil 命中 oil、said 命中 AI。英文改成整字比對
（允許 s/es 複數詞尾），中文沒有空白斷詞，維持子字串。
"""
from __future__ import annotations

import re
from functools import lru_cache


@lru_cache(maxsize=4096)
def _term_pattern(term: str) -> re.Pattern:
    escaped = re.escape(term.lower())
    return re.compile(rf"(?<![a-z0-9]){escaped}(?:s|es)?(?![a-z0-9])")


def contains_term(text: str, term: str) -> bool:
    """text 是否包含 term。text 需已轉小寫。

    - 英文（純 ASCII）詞：整字比對，允許複數詞尾（tariff → tariffs）
    - 其他（中文等）：子字串比對
    """
    if not term:
        return False
    if term.isascii():
        return _term_pattern(term).search(text) is not None
    return term in text


def count_terms(text: str, terms: list[str]) -> int:
    return sum(1 for t in terms if contains_term(text, t))


def any_term(text: str, terms: list[str]) -> bool:
    return any(contains_term(text, t) for t in terms if t)
