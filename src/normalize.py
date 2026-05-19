"""Phase 1 — normalize raw RSS into article JSON.

對應規格：
- §5.2 時間窗口（report_date 05:00 - 24h - 3h grace）
- §5.3 normalized article 格式
- §17.3 source 必含欄位

CLI 用法：
    python -m src.normalize                       # 預設今天
    python -m src.normalize --date 2026-05-18     # 指定日期

退出碼：
    0   成功
    1   raw 目錄不存在（請先跑 fetch_rss）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import feedparser
import yaml
from dateutil import parser as date_parser

LOG = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FEEDS = PROJECT_ROOT / "config" / "feeds.yaml"
DEFAULT_RAW_BASE = PROJECT_ROOT / "data" / "raw"
DEFAULT_ARTICLES_BASE = PROJECT_ROOT / "data" / "articles"

TAIPEI = timezone(timedelta(hours=8))

# 常見追蹤參數，canonicalize 時統一去掉，讓同篇文章在不同 RSS 來源產生一致的 canonical_url。
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid", "ref", "ref_src",
}


# ---------------------------------------------------------------------------
# URL canonicalization & hashing
# ---------------------------------------------------------------------------

def canonicalize_url(url: str) -> str:
    """去除追蹤參數、小寫化 scheme 與 host。"""
    if not url:
        return ""
    parsed = urlparse(url)
    cleaned_query = [
        (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]
    return urlunparse(parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        query=urlencode(cleaned_query),
    ))


def compute_article_id(source_id: str, canonical_url: str) -> str:
    """規格 §5.3: sha256(source_id + canonical_url)。重跑必須產出相同 ID。"""
    return hashlib.sha256(f"{source_id}|{canonical_url}".encode("utf-8")).hexdigest()


def compute_raw_hash(entry) -> str:
    """偵測同 URL 內容是否變更。"""
    payload = json.dumps({
        "title": entry.get("title", ""),
        "link": entry.get("link", ""),
        "summary": entry.get("summary", ""),
        "published": entry.get("published", ""),
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Time parsing & window
# ---------------------------------------------------------------------------

def parse_published(entry) -> Optional[str]:
    """從多個 RSS/Atom 時間欄位嘗試解析 published_at，回傳 +08:00 ISO 字串。"""
    for field_name in ("published", "updated", "created"):
        val = entry.get(field_name)
        if not val:
            continue
        try:
            dt = date_parser.parse(val)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(TAIPEI).isoformat()
        except (ValueError, TypeError):
            continue
    return None


def fetch_window_start(
    report_date: str,
    default_hours: int = 24,
    grace_hours: int = 3,
) -> datetime:
    """規格 §5.2: published_at >= report_date 05:00 - 24h - grace_hours."""
    date = datetime.strptime(report_date, "%Y-%m-%d").replace(
        hour=5, minute=0, second=0, microsecond=0, tzinfo=TAIPEI,
    )
    return date - timedelta(hours=default_hours + grace_hours)


def in_window(published_at: Optional[str], window_start: datetime) -> bool:
    if not published_at:
        return False
    try:
        return date_parser.parse(published_at) >= window_start
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_entry(
    entry,
    source: dict,
    fetched_at: str,
) -> Optional[dict]:
    """規格 §5.3 normalized article。缺必要欄位則回 None。"""
    title = (entry.get("title") or "").strip()
    url = (entry.get("link") or "").strip()
    published_at = parse_published(entry)

    # 規格 §4.1 required_fields: title / link / published_at
    if not title or not url or not published_at:
        return None

    canonical = canonicalize_url(url)
    return {
        "article_id": compute_article_id(source["source_id"], canonical),
        "source_id": source["source_id"],
        "publisher": source["publisher"],
        "tier": source["tier"],
        "beat_candidates": source["beats"],
        "sub_beat": source.get("sub_beat"),
        "title": title,
        "summary": entry.get("summary"),
        "url": url,
        "canonical_url": canonical,
        "published_at": published_at,
        "fetched_at": fetched_at,
        "lang": source["lang"],
        "raw_hash": compute_raw_hash(entry),
    }


def normalize_source(
    source: dict,
    raw_xml_path: Path,
    fetched_at: str,
    window_start: datetime,
) -> tuple[list[dict], int]:
    """解析一個 source 的 raw XML，輸出符合時間窗口的 article list。

    Returns:
        (articles, items_found)  -- items_found = parser 取到的 entry 總數
    """
    parsed = feedparser.parse(raw_xml_path.read_bytes())
    items_found = len(parsed.entries)

    articles: list[dict] = []
    for entry in parsed.entries:
        normalized = normalize_entry(entry, source, fetched_at)
        if normalized is None:
            continue
        if not in_window(normalized["published_at"], window_start):
            continue
        articles.append(normalized)

    return articles, items_found


def write_articles(out_dir: Path, articles: list[dict]) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    for art in articles:
        (out_dir / f"{art['article_id']}.json").write_text(
            json.dumps(art, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return len(articles)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize raw RSS into article JSON.")
    parser.add_argument("--feeds", type=Path, default=DEFAULT_FEEDS)
    parser.add_argument("--raw-base", type=Path, default=DEFAULT_RAW_BASE)
    parser.add_argument("--out-base", type=Path, default=DEFAULT_ARTICLES_BASE)
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--default-hours", type=int, default=24)
    parser.add_argument("--grace-hours", type=int, default=3)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    config = yaml.safe_load(args.feeds.read_text(encoding="utf-8"))
    sources_by_id = {s["source_id"]: s for s in config["sources"]}

    date = args.date or datetime.now(TAIPEI).strftime("%Y-%m-%d")
    raw_dir = args.raw_base / date
    out_dir = args.out_base / date

    if not raw_dir.exists():
        LOG.error("Raw directory not found: %s. Run fetch_rss first.", raw_dir)
        return 1

    health_path = raw_dir / "feed_health.json"
    health = json.loads(health_path.read_text(encoding="utf-8")) if health_path.exists() else []
    health_by_id = {h["source_id"]: h for h in health}

    window_start = fetch_window_start(date, args.default_hours, args.grace_hours)
    LOG.info("Fetch window starts at %s", window_start.isoformat())

    total = 0
    for xml_path in sorted(raw_dir.glob("*.xml")):
        source_id = xml_path.stem
        source = sources_by_id.get(source_id)
        if not source:
            LOG.warning("XML file %s has no matching source in feeds.yaml; skip.", xml_path)
            continue
        fetched_at = health_by_id.get(source_id, {}).get("fetched_at", "")
        articles, items_found = normalize_source(source, xml_path, fetched_at, window_start)
        written = write_articles(out_dir, articles)
        if source_id in health_by_id:
            health_by_id[source_id]["items_found"] = items_found
            health_by_id[source_id]["items_valid"] = written
        total += written
        LOG.info("%s: %d/%d articles within window", source_id, written, items_found)

    # 把 items_found / items_valid 回寫到 health log
    if health_by_id:
        health_path.write_text(
            json.dumps(list(health_by_id.values()), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    LOG.info("Total normalized articles: %d", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
