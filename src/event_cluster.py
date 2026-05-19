"""Phase 2 — Event clustering.

把同一事件的多篇報導合併成一則館報 item。

對應規格：
- §7.1 同一事件判定（entity、time window、語意相似度、共同關鍵詞、同 URL）
- §7.2 MVP 聚合策略（exact canonical_url / title sim 0.88 / shared kw ≥ 3 / 24h window）
- §7.3 event 格式
- §9.2 confidence 分級

MVP 簡化：
- 不做 named entity recognition；用「shared keywords ≥ 3」當替代訊號
- 不做 embedding；用 rapidfuzz token_set_ratio

CLI 用法：
    python -m src.event_cluster --date 2026-05-19
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from dateutil import parser as date_parser
from rapidfuzz import fuzz

LOG = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ARTICLES_BASE = PROJECT_ROOT / "data" / "articles"
DEFAULT_EVENTS_BASE = PROJECT_ROOT / "data" / "events"

TAIPEI = timezone(timedelta(hours=8))

# 規格 §7.2 預設值
TITLE_SIMILARITY_THRESHOLD = 88
SHARED_KEYWORDS_MIN = 3
TIME_WINDOW_HOURS = 24

# 極簡英文停用詞（MVP）
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "of", "in", "on", "at",
    "to", "for", "with", "from", "by", "as", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "should", "could", "may", "might", "can", "this",
    "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "what", "which", "who", "whom", "whose", "where", "when", "why", "how",
    "not", "no", "nor", "so", "than", "then", "their", "his", "her", "its",
    "our", "your", "my", "me", "him", "us", "them", "about", "after",
    "before", "into", "out", "over", "under", "again", "once", "any",
    "all", "some", "such", "only", "own", "same", "too", "very", "just",
    "says", "said", "say", "new", "more", "most",
}


def normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    return re.sub(r"\s+", " ", t).strip()


def extract_keywords(text: str) -> set[str]:
    """抽取英文內容詞（去停用詞、長度 > 2）。"""
    tokens = re.findall(r"[a-z][a-z\-']+", text.lower())
    return {t for t in tokens if len(t) > 2 and t not in STOPWORDS}


def article_keywords(article: dict) -> set[str]:
    text = (article.get("title", "") + " " + (article.get("summary") or ""))
    return extract_keywords(text)


def within_time_window(a: dict, b: dict, hours: int = TIME_WINDOW_HOURS) -> bool:
    """兩篇 published_at 差距 ≤ hours。"""
    try:
        ta = date_parser.parse(a["published_at"])
        tb = date_parser.parse(b["published_at"])
        return abs((ta - tb).total_seconds()) <= hours * 3600
    except (ValueError, TypeError, KeyError):
        return False


def matches_cluster(
    article: dict,
    cluster_articles: list[dict],
    title_threshold: int = TITLE_SIMILARITY_THRESHOLD,
    shared_kw_min: int = SHARED_KEYWORDS_MIN,
    time_window_hours: int = TIME_WINDOW_HOURS,
) -> bool:
    """檢查 article 是否屬於某既有 cluster。"""
    a_canonical = article.get("canonical_url", "")
    a_norm_title = normalize_title(article.get("title", ""))
    a_keywords = article_keywords(article)

    for existing in cluster_articles:
        # 規格 §7.1.5：canonical URL 完全相同 → 同篇（保險，dedup 通常已處理）
        if a_canonical and a_canonical == existing.get("canonical_url"):
            return True

        # 規格 §7.1.2：時間窗口必須先成立
        if not within_time_window(article, existing, time_window_hours):
            continue

        # 規格 §7.2：標題正規化相似度 ≥ 0.88
        existing_norm = normalize_title(existing.get("title", ""))
        if fuzz.token_set_ratio(a_norm_title, existing_norm) >= title_threshold:
            return True

        # 規格 §7.2：共同關鍵詞 ≥ 3
        shared = a_keywords & article_keywords(existing)
        if len(shared) >= shared_kw_min:
            return True

    return False


def cluster_articles(
    articles: list[dict],
    title_threshold: int = TITLE_SIMILARITY_THRESHOLD,
    shared_kw_min: int = SHARED_KEYWORDS_MIN,
    time_window_hours: int = TIME_WINDOW_HOURS,
) -> list[list[dict]]:
    """把 articles 聚合成 clusters。每個 cluster 是 article list。

    PTS_LOCAL 來源不與其他 beat 合併（規格 §2.2）。
    """
    clusters: list[list[dict]] = []
    # 按 published_at 排序，較舊先處理
    sorted_articles = sorted(articles, key=lambda a: a.get("published_at", ""))

    for art in sorted_articles:
        matched = None
        for cluster in clusters:
            # PTS_LOCAL 隔離：兩邊 beat 必須一致才能合
            if (art.get("beat") == "PTS_LOCAL") != (cluster[0].get("beat") == "PTS_LOCAL"):
                continue
            if matches_cluster(art, cluster, title_threshold, shared_kw_min, time_window_hours):
                matched = cluster
                break
        if matched is not None:
            matched.append(art)
        else:
            clusters.append([art])

    return clusters


# ---------------------------------------------------------------------------
# Cluster → Event
# ---------------------------------------------------------------------------

def derive_confidence(cluster: list[dict]) -> str:
    """規格 §9.2：
    - high: ≥2 Tier 1/2 sources
    - low: 單一 Tier 3 source
    - medium: 其他
    """
    tiers = [a.get("tier") for a in cluster]
    distinct_sources = {a.get("source_id") for a in cluster}
    high_tier_count = sum(1 for t in tiers if t in (1, 2))

    if len(distinct_sources) >= 2 and high_tier_count >= 2:
        return "high"
    if len(distinct_sources) == 1 and tiers[0] == 3:
        return "low"
    return "medium"


def derive_beat(cluster: list[dict]) -> Optional[str]:
    """取 cluster 中最常見的 beat。"""
    beats = [a.get("beat") for a in cluster if a.get("beat")]
    if not beats:
        return None
    return Counter(beats).most_common(1)[0][0]


def derive_sub_beat(cluster: list[dict]) -> Optional[str]:
    sub_beats = [a.get("sub_beat") for a in cluster if a.get("sub_beat")]
    if not sub_beats:
        return None
    return Counter(sub_beats).most_common(1)[0][0]


def merge_tw_highlight(cluster: list[dict]) -> tuple[bool, Optional[str], list[str]]:
    """若 cluster 任一篇 tw_highlight=true，整個 event 即為 highlight。"""
    flagged = [a for a in cluster if a.get("tw_highlight")]
    if not flagged:
        return False, None, []
    reasons = [a.get("tw_highlight_reason") for a in flagged if a.get("tw_highlight_reason")]
    keywords: list[str] = []
    for a in flagged:
        keywords.extend(a.get("tw_highlight_keywords") or [])
    # dedupe while preserving order
    seen = set()
    deduped_kws = [k for k in keywords if not (k in seen or seen.add(k))]
    return True, "; ".join(reasons) if reasons else None, deduped_kws


def build_event(
    cluster: list[dict],
    event_id: str,
) -> dict:
    """規格 §7.3 event 格式。

    headline / context / claim_trace 的最終文字在 Phase 3 由 Claude 改寫覆蓋；
    這裡先用代表性文章的資料填初稿，使 event 即時通過 event.schema.json。
    """
    rep = cluster[0]  # 用最早一篇當代表
    beat = derive_beat(cluster) or rep.get("beat") or "INTL"
    sub_beat = derive_sub_beat(cluster)
    confidence = derive_confidence(cluster)
    tw_flag, tw_reason, tw_keywords = merge_tw_highlight(cluster)

    # 同源同 URL 視為同一 source（取每個 unique source_id 的第一篇）
    sources_by_id: dict[str, dict] = {}
    for a in cluster:
        sid = a["source_id"]
        if sid not in sources_by_id:
            sources_by_id[sid] = {
                "source_id": sid,
                "name": sid.replace("_", " ").title(),
                "publisher": a.get("publisher", ""),
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "published_at": a.get("published_at", ""),
            }
    sources = list(sources_by_id.values())
    source_count = len(sources)
    source_tiers = sorted({a.get("tier") for a in cluster if a.get("tier") is not None},
                          key=lambda t: (isinstance(t, str), t))
    single_source_warning = source_count == 1

    # 規格 §17 + §20.1：每個 selected item 至少 1 條 claim_trace；
    # 此處先以原始來源標題作為占位 claim，Phase 3 Claude 會重寫。
    claim_trace = [
        {
            "claim": a.get("title", ""),
            "source_id": a["source_id"],
            "source_title": a.get("title", ""),
            "source_url": a.get("url", ""),
            "support_type": "direct",
        }
        for a in cluster
    ]

    return {
        "event_id": event_id,
        "beat": beat,
        "sub_beat": sub_beat,
        "headline": rep.get("title", ""),
        "context": (rep.get("summary") or rep.get("title", ""))[:280],
        "article_ids": [a["article_id"] for a in cluster],
        "sources": sources,
        "source_count": source_count,
        "source_tiers": source_tiers,
        "tw_highlight": tw_flag,
        "tw_highlight_reason": tw_reason,
        "tw_highlight_keywords": tw_keywords or None,
        "selection_score": 0,  # 由 selector 填
        "selection_reason": None,
        "drop_reason": None,
        "confidence": confidence,
        "single_source_warning": single_source_warning,
        "opinion_level": "none",
        "claim_trace": claim_trace,
    }


def cluster_to_events(
    articles: list[dict],
    date_str: str,
    **cluster_kwargs,
) -> list[dict]:
    """主入口：clusters → events list。"""
    clusters = cluster_articles(articles, **cluster_kwargs)
    date_compact = date_str.replace("-", "")
    return [
        build_event(c, f"daily_{date_compact}_evt_{i+1:03d}")
        for i, c in enumerate(clusters)
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Cluster articles into events.")
    parser.add_argument("--articles-base", type=Path, default=DEFAULT_ARTICLES_BASE)
    parser.add_argument("--events-base", type=Path, default=DEFAULT_EVENTS_BASE)
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--title-threshold", type=int, default=TITLE_SIMILARITY_THRESHOLD)
    parser.add_argument("--shared-kw-min", type=int, default=SHARED_KEYWORDS_MIN)
    parser.add_argument("--time-window-hours", type=int, default=TIME_WINDOW_HOURS)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    date = args.date or datetime.now(TAIPEI).strftime("%Y-%m-%d")
    articles_dir = args.articles_base / date
    events_dir = args.events_base / date

    if not articles_dir.exists():
        LOG.error("Articles directory not found: %s", articles_dir)
        return 1

    files = sorted(articles_dir.glob("*.json"))
    articles = [json.loads(fp.read_text(encoding="utf-8")) for fp in files
                if not fp.name.startswith("_")]
    # 只聚合已分類成功的文章
    articles = [a for a in articles if a.get("beat")]

    events = cluster_to_events(
        articles,
        date,
        title_threshold=args.title_threshold,
        shared_kw_min=args.shared_kw_min,
        time_window_hours=args.time_window_hours,
    )

    events_dir.mkdir(parents=True, exist_ok=True)
    for evt in events:
        (events_dir / f"{evt['event_id']}.json").write_text(
            json.dumps(evt, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    multi = sum(1 for e in events if e["source_count"] >= 2)
    tw = sum(1 for e in events if e["tw_highlight"])
    LOG.info("Articles: %d → Events: %d (%d multi-source, %d TW highlight)",
             len(articles), len(events), multi, tw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
