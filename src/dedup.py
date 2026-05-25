"""Phase 2 — Article-level dedup.

對應規格 §5.1（pipeline 中的 dedup_articles 步驟）。

注意：本檔處理的是**同一篇文章** 的去重（同 URL / 同源同題等）。
跨來源的同一事件聚合走 `src/event_cluster.py`。

判斷規則：
- canonical_url 完全相同 → 同篇
- 同來源 + 標題正規化相似度 ≥ 0.92 → 同篇（保守，避免砍到不同新聞）

CLI 用法：
    python -m src.dedup --date 2026-05-19
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from rapidfuzz import fuzz

LOG = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ARTICLES_BASE = PROJECT_ROOT / "data" / "articles"

TAIPEI = timezone(timedelta(hours=8))

# 注意：article-level dedup 用較高門檻；event cluster 用較低門檻。
ARTICLE_DEDUP_THRESHOLD = 92


def normalize_title(title: str) -> str:
    """小寫、去標點、collapse 空白。"""
    t = title.lower()
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def dedup_articles(
    articles: list[dict],
    threshold: int = ARTICLE_DEDUP_THRESHOLD,
) -> tuple[list[dict], list[dict]]:
    """去除重複文章。

    Returns:
        (unique_articles, dropped)
        dropped: [{'article_id': ..., 'duplicate_of': ..., 'reason': ...}, ...]
    """
    unique: list[dict] = []
    dropped: list[dict] = []

    # 1. canonical_url 索引：第一次出現即記住
    seen_canonical: dict[str, str] = {}
    # 2. 同源標題索引：source_id -> [(normalized_title, article_id)]
    seen_titles: dict[str, list[tuple[str, str]]] = {}

    for art in articles:
        aid = art["article_id"]
        canonical = art.get("canonical_url", "")
        source_id = art.get("source_id", "")
        norm_title = normalize_title(art.get("title", ""))

        # Rule 1: canonical URL exact match
        if canonical and canonical in seen_canonical:
            dropped.append({
                "article_id": aid,
                "duplicate_of": seen_canonical[canonical],
                "reason": "exact_canonical_url",
            })
            continue

        # Rule 2: same source + similar title
        same_source_titles = seen_titles.get(source_id, [])
        matched_id = None
        for existing_title, existing_id in same_source_titles:
            score = fuzz.ratio(norm_title, existing_title)
            if score >= threshold:
                matched_id = existing_id
                break
        if matched_id:
            dropped.append({
                "article_id": aid,
                "duplicate_of": matched_id,
                "reason": "same_source_similar_title",
            })
            continue

        # Keep
        unique.append(art)
        if canonical:
            seen_canonical[canonical] = aid
        seen_titles.setdefault(source_id, []).append((norm_title, aid))

    return unique, dropped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Deduplicate normalized articles.")
    parser.add_argument("--articles-base", type=Path, default=DEFAULT_ARTICLES_BASE)
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--threshold", type=int, default=ARTICLE_DEDUP_THRESHOLD)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    date = args.date or datetime.now(TAIPEI).strftime("%Y-%m-%d")
    articles_dir = args.articles_base / date

    if not articles_dir.exists():
        LOG.error("Articles directory not found: %s", articles_dir)
        return 1

    files = sorted(f for f in articles_dir.glob("*.json")
                   if not f.name.startswith("_"))
    articles = [json.loads(fp.read_text(encoding="utf-8")) for fp in files]

    unique, dropped = dedup_articles(articles, args.threshold)

    LOG.info("Total: %d, unique: %d, dropped: %d", len(articles), len(unique), len(dropped))
    for d in dropped[:10]:
        LOG.info("  DROP %s (reason: %s, dup_of=%s)",
                 d["article_id"][:12], d["reason"], d["duplicate_of"][:12])

    if not args.dry_run:
        dropped_ids = {d["article_id"] for d in dropped}
        for fp in files:
            aid = fp.stem
            if aid in dropped_ids:
                fp.unlink()
        # Persist drop log
        log_path = articles_dir / "_dedup_log.json"
        log_path.write_text(
            json.dumps(dropped, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        LOG.info("Drop log: %s", log_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
