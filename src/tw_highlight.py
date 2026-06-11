"""Phase 2 — Taiwan Highlight 偵測。

對應規格 §6.3 / §6.4：
- positive_keywords：indicates Taiwan-related mention
- context_keywords：indicates public importance
- false_positive_review：常見假陽性樣式

判定流程：
1. 沒有任何 positive_keyword → 不 highlight
2. 命中 false_positive 樣式且沒有任何 context_keyword 加持 → 不 highlight
3. 沒有任何 context_keyword → 不 highlight（只是順帶提一句台灣）
4. 同時有 positive 與 context → highlight=true，記錄 reason 與 keywords

CLI 用法：
    python -m src.tw_highlight --date 2026-05-19
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import yaml

LOG = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BEATS_CONFIG = PROJECT_ROOT / "config" / "beats.yaml"
DEFAULT_ARTICLES_BASE = PROJECT_ROOT / "data" / "articles"

TAIPEI = timezone(timedelta(hours=8))


def load_tw_config(beats_config_path: Path) -> dict:
    with beats_config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f).get("tw_highlight", {})


def detect(
    article: dict,
    tw_config: dict,
) -> tuple[bool, Optional[str], list[str]]:
    """規格 §6.3 / §6.4。

    Returns:
        (tw_highlight, tw_highlight_reason, tw_highlight_keywords)
    """
    text = (article.get("title", "") + " " + (article.get("summary") or "")).lower()

    positive = tw_config.get("positive_keywords", []) or []
    context = tw_config.get("context_keywords", []) or []
    fps = tw_config.get("false_positive_review", []) or []

    matched_positive = [k for k in positive if k.lower() in text]
    if not matched_positive:
        return False, None, []

    matched_fps = [fp for fp in fps if fp.lower() in text]
    matched_context = [k for k in context if k.lower() in text]

    # 規格 §6.3 隱含邏輯：FP 命中但無 context 加持 → 視為非 highlight
    if matched_fps and not matched_context:
        return False, None, []

    # 沒命中任何 context_keyword → 只是順帶提台灣，不算 highlight
    if not matched_context:
        return False, None, []

    keywords = matched_positive + matched_context
    primary = matched_positive[0]
    ctx_str = "、".join(matched_context[:3])
    reason = f"Mentions {primary} in context of {ctx_str}."
    return True, reason, keywords


def annotate(article: dict, tw_config: dict) -> dict:
    """回傳帶 tw_highlight 三欄位的新 article dict（不改原物件）。"""
    flag, reason, kws = detect(article, tw_config)
    enriched = dict(article)
    enriched["tw_highlight"] = flag
    enriched["tw_highlight_reason"] = reason
    enriched["tw_highlight_keywords"] = kws
    return enriched


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Detect Taiwan-related highlights.")
    parser.add_argument("--beats-config", type=Path, default=DEFAULT_BEATS_CONFIG)
    parser.add_argument("--articles-base", type=Path, default=DEFAULT_ARTICLES_BASE)
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    tw_config = load_tw_config(args.beats_config)
    date = args.date or datetime.now(TAIPEI).strftime("%Y-%m-%d")
    articles_dir = args.articles_base / date

    if not articles_dir.exists():
        LOG.error("Articles directory not found: %s", articles_dir)
        return 1

    highlights = 0
    files = sorted(f for f in articles_dir.glob("*.json")
                   if not f.name.startswith("_"))
    for fp in files:
        article = json.loads(fp.read_text(encoding="utf-8"))
        enriched = annotate(article, tw_config)
        if enriched["tw_highlight"]:
            highlights += 1
            LOG.info("  HIGHLIGHT  %s — %s", article["source_id"], article["title"])
        if not args.dry_run:
            fp.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")

    LOG.info("Annotated %d articles; %d TW highlights", len(files), highlights)
    return 0


if __name__ == "__main__":
    sys.exit(main())
