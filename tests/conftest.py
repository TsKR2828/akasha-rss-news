"""共用 pytest fixtures。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = PROJECT_ROOT / "schemas"


def _load(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def article_schema() -> dict:
    return _load("article.schema.json")


@pytest.fixture(scope="session")
def event_schema() -> dict:
    return _load("event.schema.json")


@pytest.fixture(scope="session")
def platform_output_schema() -> dict:
    return _load("platform_output.schema.json")


@pytest.fixture(scope="session")
def report_schema() -> dict:
    return _load("report.schema.json")


@pytest.fixture(scope="session")
def all_schemas(
    article_schema, event_schema, platform_output_schema, report_schema
) -> dict[str, dict]:
    return {
        "article.schema.json": article_schema,
        "event.schema.json": event_schema,
        "platform_output.schema.json": platform_output_schema,
        "report.schema.json": report_schema,
    }


# ---------- Sample fixtures ----------
# 對應規格 §5.3 / §7.3 / §11.2 / §11.3

@pytest.fixture
def sample_article() -> dict:
    return {
        "article_id": "a" * 64,
        "source_id": "bbc_world",
        "publisher": "BBC",
        "tier": 1,
        "beat_candidates": ["INTL"],
        "sub_beat": None,
        "title": "Sample headline",
        "summary": "Sample summary.",
        "url": "https://www.bbc.com/news/world-12345",
        "canonical_url": "https://www.bbc.com/news/world-12345",
        "published_at": "2026-05-18T01:20:00+08:00",
        "fetched_at": "2026-05-18T05:01:00+08:00",
        "lang": "en",
        "raw_hash": "b" * 64,
    }


@pytest.fixture
def sample_source_ref() -> dict:
    return {
        "source_id": "bbc_world",
        "name": "BBC World",
        "publisher": "BBC",
        "title": "Sample headline",
        "url": "https://www.bbc.com/news/world-12345",
        "published_at": "2026-05-18T01:20:00+08:00",
    }


@pytest.fixture
def sample_claim() -> dict:
    return {
        "claim": "事件核心事實。",
        "source_id": "bbc_world",
        "source_title": "Sample headline",
        "source_url": "https://www.bbc.com/news/world-12345",
        "support_type": "direct",
    }


@pytest.fixture
def sample_event(sample_source_ref, sample_claim) -> dict:
    return {
        "event_id": "daily_20260518_evt_001",
        "beat": "INTL",
        "sub_beat": None,
        "headline": "事件標題",
        "context": "2-3 句脈絡說明。",
        "article_ids": ["a" * 64, "c" * 64],
        "sources": [sample_source_ref, {**sample_source_ref, "source_id": "reuters_world_google_news"}],
        "source_count": 2,
        "source_tiers": [1, 1],
        "tw_highlight": False,
        "tw_highlight_reason": None,
        "tw_highlight_keywords": None,
        "selection_score": 78,
        "selection_reason": "Tier 1 多來源確認。",
        "drop_reason": None,
        "confidence": "high",
        "single_source_warning": False,
        "opinion_level": "none",
        "claim_trace": [sample_claim],
    }


@pytest.fixture
def sample_platform_item(sample_source_ref, sample_claim) -> dict:
    return {
        "event_id": "daily_20260518_evt_001",
        "headline": "事件標題",
        "context": "脈絡說明。",
        "beat": "INTL",
        "sub_beat": None,
        "thread_text": "X 版完整內文。",
        "threads_text": "Threads 版完整內文。",
        "voice_text": "朗讀版內文，沒有任何網址或表情符號。",
        "platform_outputs": {
            "x": {
                "max_chars": 280,
                "posts": ["🧵 1/2\n📌 國際大事\n\n事件標題。", "—— 來自 BBC。"],
            },
            "threads": {
                "max_chars": 500,
                "posts": ["完整 Threads 貼文。"],
            },
            "voice": {"text": "朗讀版內文，沒有任何網址或表情符號。"},
        },
        "sources": [sample_source_ref],
        "source_count": 1,
        "confidence": "medium",
        "single_source_warning": True,
        "opinion_level": "light_context",
        "claim_trace": [sample_claim],
        "tw_highlight": False,
        "tw_highlight_reason": None,
        "selection_score": 70,
        "selection_reason": "Tier 1 single source.",
    }


@pytest.fixture
def sample_report(sample_platform_item) -> dict:
    return {
        "reportId": "daily_20260518",
        "date": "2026-05-18",
        "timezone": "Asia/Taipei",
        "generated_at": "2026-05-18T05:15:00+08:00",
        "status": "ok",
        "warnings": [],
        "sections": [
            {"beat": "INTL", "title": "國際大事", "emoji": "🌍", "items": [sample_platform_item]},
            {"beat": "ARTS", "title": "八大藝術", "emoji": "🎭", "items": []},
            {"beat": "AI", "title": "AI 新知", "emoji": "🤖", "items": []},
            {"beat": "ECON", "title": "全球經濟趨勢", "emoji": "📊", "items": []},
            {"beat": "PTS_LOCAL", "title": "公視在地新聞", "emoji": "🇹🇼", "items": []},
            {"beat": "TW_STORY", "title": "今日台灣故事", "emoji": "📜", "items": []},
        ],
        "stats": {
            "total_feeds_checked": 28,
            "total_feeds_failed": 0,
            "total_articles_fetched": 320,
            "total_articles_after_filter": 180,
            "total_events_merged": 60,
            "total_events_selected": 12,
            "tw_highlights_count": 1,
        },
        "voiceTaskId": None,
        "bgmScoreId": None,
    }
