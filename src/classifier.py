"""Phase 2 — Beat 分類。

對應規格：
- §2.1 四大常駐區塊（INTL / ARTS / AI / ECON / PTS_LOCAL）
- §6.1 分類權重（source 0.6 + keyword 0.3 + entity 0.1，min_score 0.45）
- §6.2 AI 分類例外（The Verge / BBC Tech / Ars Technica 需二次過濾）

entity_weight 透過 spaCy NER 提取實體，與 beats.yaml 中各 beat 的
entities.entity_names / entity_types 比對。若 spaCy 未安裝則回退為 0。

CLI 用法：
    python -m src.classifier --date 2026-05-19
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

import yaml

from src import entity_recognizer

LOG = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BEATS_CONFIG = PROJECT_ROOT / "config" / "beats.yaml"
DEFAULT_ARTICLES_BASE = PROJECT_ROOT / "data" / "articles"

TAIPEI = timezone(timedelta(hours=8))

# 規格 §2.2 特別標記，不參與一般 beat 分類
SKIP_BEATS = {"TW_HIGHLIGHT", "TW_STORY"}


def load_beats_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _tokenize(text: str) -> list[str]:
    """Lowercase, 抽取英文單字（用於關鍵字比對）。"""
    return re.findall(r"[a-z][a-z\-']+", text.lower())


def keyword_match_score(article: dict, beat_def: dict) -> float:
    """命中率：article 標題+摘要中出現幾個 beat 關鍵字 / 該 beat 關鍵字總數。

    上限為 1.0；考慮短文章常只命中 1-2 個，因此再 normalize 一次：
    只要命中 ≥ 2 個關鍵字就視為 1.0；命中 1 個視為 0.5；0 個是 0.0。
    """
    text = (article.get("title", "") + " " + (article.get("summary") or "")).lower()
    keywords_en = beat_def.get("keywords_en", []) or []
    keywords_zh = beat_def.get("keywords_zh", []) or []

    en_hits = sum(1 for kw in keywords_en if kw.lower() in text)
    zh_hits = sum(1 for kw in keywords_zh if kw in text)
    total_hits = en_hits + zh_hits

    if total_hits >= 2:
        return 1.0
    if total_hits == 1:
        return 0.5
    return 0.0


def _has_ai_keyword(article: dict, ai_beat_def: dict) -> bool:
    """規格 §6.2：AI beat 例外規則。

    至少符合：
    - title / summary 命中 AI 關鍵字
    - 出現模型、AI 公司、AI 法規、AI 研究主題
    """
    text = (article.get("title", "") + " " + (article.get("summary") or "")).lower()
    return any(kw.lower() in text for kw in ai_beat_def.get("keywords_en", []))


def _has_econ_keyword(article: dict, econ_beat_def: dict) -> bool:
    """ECON beat 例外規則（同 AI §6.2 模式）。

    商業類 RSS 常夾帶非經濟新聞（空難、機場擴建等），
    例外來源須 title/summary 命中 ECON 關鍵字才算 ECON。
    """
    text = (article.get("title", "") + " " + (article.get("summary") or "")).lower()
    keywords_en = econ_beat_def.get("keywords_en", [])
    keywords_zh = econ_beat_def.get("keywords_zh", [])
    return (any(kw.lower() in text for kw in keywords_en) or
            any(kw in text for kw in keywords_zh))


def classify(
    article: dict,
    beats_config: dict,
    min_score: Optional[float] = None,
) -> tuple[Optional[str], dict[str, float]]:
    """規格 §6.1 分類。

    Returns:
        (primary_beat, beat_scores)
        primary_beat: 最高分 beat；若全部低於 min_score 則回 None
        beat_scores: {beat_id: score}
    """
    cfg = beats_config.get("classification", {})
    sw = cfg.get("source_default_weight", 0.6)
    kw = cfg.get("keyword_weight", 0.3)
    ew = cfg.get("entity_weight", 0.1)  # MVP: 不計算
    threshold = cfg.get("min_score", 0.45) if min_score is None else min_score

    source_beats = set(article.get("beat_candidates", []))
    ai_exception_sources = set(beats_config.get("ai_exception_sources", []))
    econ_exception_sources = set(beats_config.get("econ_exception_sources", []))
    beats = beats_config.get("beats", {})

    # 提取一次實體，供所有 beat 共用
    text = (article.get("title", "") + " " + (article.get("summary") or ""))
    entities = entity_recognizer.extract_entities(text)

    scores: dict[str, float] = {}
    for beat_id, beat_def in beats.items():
        if beat_id in SKIP_BEATS:
            continue

        source_score = 1.0 if beat_id in source_beats else 0.0
        kw_score = keyword_match_score(article, beat_def)
        entity_score = entity_recognizer.entity_match_score(
            entities, beat_def.get("entities", {}),
        )

        # 規格 §6.2: AI 例外 — 例外來源若 title/summary 沒命中 AI 關鍵字，AI 該篇降權
        if (
            beat_id == "AI"
            and article.get("source_id") in ai_exception_sources
            and not _has_ai_keyword(article, beat_def)
        ):
            scores[beat_id] = 0.0
            continue

        # ECON 例外 — 商業來源若 title/summary 沒命中 ECON 關鍵字，ECON 該篇降權
        if (
            beat_id == "ECON"
            and article.get("source_id") in econ_exception_sources
            and not _has_econ_keyword(article, beat_def)
        ):
            scores[beat_id] = 0.0
            continue

        scores[beat_id] = sw * source_score + kw * kw_score + ew * entity_score

    # PTS_LOCAL: 來源是公視 → 直接歸 PTS_LOCAL，不參與 INTL/ARTS/AI/ECON 競爭
    if "PTS_LOCAL" in source_beats:
        return "PTS_LOCAL", scores | {"PTS_LOCAL": 1.0}

    if not scores:
        return None, {}

    primary = max(scores, key=scores.get)
    if scores[primary] < threshold:
        return None, scores
    return primary, scores


def classify_article(article: dict, beats_config: dict) -> dict:
    """回傳帶 `beat` 與 `beat_scores` 的新 article dict（不改原物件）。"""
    primary, scores = classify(article, beats_config)
    enriched = dict(article)
    enriched["beat"] = primary
    enriched["beat_scores"] = {k: round(v, 3) for k, v in scores.items()}
    return enriched


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Classify normalized articles by beat.")
    parser.add_argument("--beats-config", type=Path, default=DEFAULT_BEATS_CONFIG)
    parser.add_argument("--articles-base", type=Path, default=DEFAULT_ARTICLES_BASE)
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true",
                        help="只印統計，不寫回檔案")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    beats_config = load_beats_config(args.beats_config)
    date = args.date or datetime.now(TAIPEI).strftime("%Y-%m-%d")
    articles_dir = args.articles_base / date

    if not articles_dir.exists():
        LOG.error("Articles directory not found: %s", articles_dir)
        return 1

    counts: dict[str, int] = {}
    rejected = 0
    files = sorted(articles_dir.glob("*.json"))

    for fp in files:
        article = json.loads(fp.read_text(encoding="utf-8"))
        enriched = classify_article(article, beats_config)
        beat = enriched["beat"]
        if beat is None:
            rejected += 1
        else:
            counts[beat] = counts.get(beat, 0) + 1
        if not args.dry_run:
            fp.write_text(
                json.dumps(enriched, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    LOG.info("Classified %d articles", len(files))
    for beat, n in sorted(counts.items(), key=lambda x: -x[1]):
        LOG.info("  %-10s %d", beat, n)
    if rejected:
        LOG.info("  %-10s %d (below min_score)", "(rejected)", rejected)

    return 0


if __name__ == "__main__":
    sys.exit(main())
