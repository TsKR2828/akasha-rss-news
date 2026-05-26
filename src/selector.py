"""Phase 2 — selection_score 計算與選題。

對應規格：
- §8.1 daily_limits（每 beat min/max）
- §8.2 selection_score（多來源 +30、台灣相關外媒報導 +30、八卦 -50 …）
- §8.3 drop_reason

MVP 簡化：
- 「major_geopolitical_event / arts_major_award / ai_major_model / economy_macro_policy」用
  關鍵字啟發式判斷（同 beat 命中信號詞即加分）。
- 「direct_public_impact / celebrity_gossip / crime_without_global_relevance /
  press_release_only」需語意理解，MVP 先不算（或留 hook 給未來模組）。
- 「same_topic_already_selected」在排序後依「共同關鍵詞數」判斷。

CLI 用法：
    python -m src.selector --date 2026-05-19
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

from src.event_cluster import article_keywords, extract_keywords

LOG = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCORE_CONFIG = PROJECT_ROOT / "config" / "selection_score.yaml"
DEFAULT_EVENTS_BASE = PROJECT_ROOT / "data" / "events"

TAIPEI = timezone(timedelta(hours=8))

# Beat 內容信號詞（MVP 啟發式）
BEAT_SIGNAL_KEYWORDS = {
    "INTL": ["war", "conflict", "summit", "treaty", "sanctions", "ceasefire",
             "election", "coup", "missile", "refugee", "nato", "un security"],
    "ARTS": ["pulitzer", "booker", "cannes", "venice biennale", "oscar",
             "tony award", "grammy", "moma", "tate", "guggenheim"],
    "AI": ["gpt", "claude", "gemini", "llama", "foundation model", "agi",
           "open source", "regulation", "ai act", "transformer"],
    "ECON": ["fed", "ecb", "interest rate", "gdp", "inflation", "recession",
             "tariff", "supply chain", "semiconductor", "opec", "yield curve"],
}

# Taiwan source 識別（用來判斷 taiwan_related_foreign_report：非台灣源 + tw_highlight）
TAIWAN_SOURCE_PREFIXES = ("pts_",)


def load_score_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _is_foreign_source(source_id: str) -> bool:
    return not source_id.startswith(TAIWAN_SOURCE_PREFIXES)


def _signal_keyword_hit(event: dict) -> bool:
    beat = event.get("beat")
    signals = BEAT_SIGNAL_KEYWORDS.get(beat, [])
    if not signals:
        return False
    text = (event.get("headline", "") + " " + (event.get("context") or "")).lower()
    return any(s in text for s in signals)


def score_event(event: dict, score_config: dict) -> tuple[int, list[str]]:
    """規格 §8.2。

    Returns:
        (score, applied_rules) — applied_rules 用於 selection_reason 顯示。
    """
    weights = score_config.get("selection_score", {})
    score = 0
    applied: list[str] = []

    # --- 正分 ---
    if event.get("source_count", 0) >= 2:
        score += weights.get("multi_source_confirmed", 0)
        applied.append("multi_source_confirmed")

    if event.get("tw_highlight"):
        sources = event.get("sources", [])
        if sources and all(_is_foreign_source(s["source_id"]) for s in sources):
            score += weights.get("taiwan_related_foreign_report", 0)
            applied.append("taiwan_related_foreign_report")

    for tier in event.get("source_tiers", []):
        if tier == 1 or tier == "TW":
            score += weights.get("source_tier_1", 0)
            applied.append("source_tier_1")
        elif tier == 2:
            score += weights.get("source_tier_2", 0)
            applied.append("source_tier_2")
        elif tier == 3:
            score += weights.get("source_tier_3", 0)
            applied.append("source_tier_3")

    # Beat-specific 啟發式加分
    if _signal_keyword_hit(event):
        beat = event.get("beat")
        if beat == "INTL":
            score += weights.get("major_geopolitical_event", 0)
            applied.append("major_geopolitical_event")
        elif beat == "ARTS":
            score += weights.get("arts_major_award_or_institution", 0)
            applied.append("arts_major_award_or_institution")
        elif beat == "AI":
            score += weights.get("ai_major_model_or_policy", 0)
            applied.append("ai_major_model_or_policy")
        elif beat == "ECON":
            score += weights.get("economy_macro_policy", 0)
            applied.append("economy_macro_policy")

    # --- 負分 ---
    if event.get("source_count", 0) == 1:
        tiers = event.get("source_tiers", [])
        if tiers and tiers[0] == 3:
            score += weights.get("single_low_tier_source", 0)
            applied.append("single_low_tier_source")

    return score, applied


def select_events(
    events: list[dict],
    score_config: dict,
) -> tuple[list[dict], list[dict]]:
    """依 selection_score 排序 + daily_limits 篩選。

    Returns:
        (selected, dropped) — selected 已更新 selection_score / selection_reason
        dropped 已更新 selection_score / drop_reason
    """
    daily_limits = score_config.get("daily_limits", {})
    same_topic_penalty = score_config.get("selection_score", {}).get(
        "same_topic_already_selected", -20,
    )

    # 1. 算分
    scored: list[tuple[int, list[str], dict]] = []
    for e in events:
        s, rules = score_event(e, score_config)
        scored.append((s, rules, e))

    # 2. 按分數降序處理；同分按 multi-source > tier 高 > 早發布
    scored.sort(
        key=lambda x: (
            -x[0],
            -x[2].get("source_count", 0),
            min((t if isinstance(t, int) else 1 for t in x[2].get("source_tiers", [99])), default=99),
            x[2].get("event_id", ""),
        )
    )

    selected_by_beat: dict[str, list[dict]] = {}
    dropped: list[dict] = []
    selected_keyword_sets: list[set[str]] = []  # 已選事件的 keyword set，用來判 same_topic

    for s, rules, e in scored:
        beat = e.get("beat")
        limits = daily_limits.get(beat, {})
        max_cnt = limits.get("max", 999)
        already = selected_by_beat.get(beat, [])

        # 計算 final_score（包含 same_topic_already_selected 動態調整）
        final_score = s
        final_rules = list(rules)
        event_kws = extract_keywords(
            (e.get("headline", "") + " " + (e.get("context") or ""))
        )
        if any(len(event_kws & prev) >= 3 for prev in selected_keyword_sets):
            final_score += same_topic_penalty
            final_rules.append("same_topic_already_selected")

        e["selection_score"] = final_score
        e["selection_reason"] = "; ".join(final_rules) if final_rules else None

        if len(already) >= max_cnt:
            e["drop_reason"] = "beat_limit_reached"
            dropped.append(e)
            continue

        already.append(e)
        selected_by_beat[beat] = already
        selected_keyword_sets.append(event_kws)

    # 3. flatten — beat 順序為 INTL, ARTS, AI, ECON, PTS_LOCAL, TW_STORY
    beat_order = ["INTL", "ARTS", "AI", "ECON", "PTS_LOCAL", "TW_STORY"]
    selected: list[dict] = []
    for b in beat_order:
        selected.extend(selected_by_beat.get(b, []))
    # 其他 beat（例如 None）放最後
    for b, items in selected_by_beat.items():
        if b not in beat_order:
            selected.extend(items)

    # 4. total_events.max enforcement (protect beat min)
    total_limits = daily_limits.get("total_events", {})
    total_max = total_limits.get("max", 999)
    if len(selected) > total_max:
        beat_counts: dict[str, int] = {}
        for e in selected:
            b = e.get("beat", "")
            beat_counts[b] = beat_counts.get(b, 0) + 1

        by_score = sorted(selected, key=lambda e: e.get("selection_score", 0))
        to_drop = len(selected) - total_max
        drop_ids: set[str] = set()
        for e in by_score:
            if to_drop <= 0:
                break
            b = e.get("beat", "")
            b_min = daily_limits.get(b, {}).get("min", 0)
            if beat_counts.get(b, 0) > b_min:
                drop_ids.add(e["event_id"])
                e["drop_reason"] = "total_limit_reached"
                dropped.append(e)
                beat_counts[b] -= 1
                to_drop -= 1

        selected = [e for e in selected if e["event_id"] not in drop_ids]

    # 5. Advisory warnings for min shortfalls
    total_min = total_limits.get("min", 0)
    if total_min and len(selected) < total_min:
        LOG.warning("Total selected events (%d) < min (%d)", len(selected), total_min)
    for b in beat_order:
        b_min = daily_limits.get(b, {}).get("min", 0)
        b_count = sum(1 for e in selected if e.get("beat") == b)
        if b_min and b_count < b_min:
            LOG.warning("Beat %s: %d selected < min %d", b, b_count, b_min)

    return selected, dropped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Score and select events.")
    parser.add_argument("--score-config", type=Path, default=DEFAULT_SCORE_CONFIG)
    parser.add_argument("--events-base", type=Path, default=DEFAULT_EVENTS_BASE)
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    score_config = load_score_config(args.score_config)
    date = args.date or datetime.now(TAIPEI).strftime("%Y-%m-%d")
    events_dir = args.events_base / date

    if not events_dir.exists():
        LOG.error("Events directory not found: %s", events_dir)
        return 1

    files = sorted(events_dir.glob("*.json"))
    events = [json.loads(fp.read_text(encoding="utf-8")) for fp in files
              if not fp.name.startswith("_")]

    selected, dropped = select_events(events, score_config)

    LOG.info("Events: %d total → %d selected, %d dropped",
             len(events), len(selected), len(dropped))
    counts: dict[str, int] = {}
    for e in selected:
        counts[e.get("beat", "?")] = counts.get(e.get("beat", "?"), 0) + 1
    for b, n in counts.items():
        LOG.info("  %-10s %d", b, n)

    if not args.dry_run:
        # 寫回 selected events（已含 selection_score / reason）
        for e in selected + dropped:
            (events_dir / f"{e['event_id']}.json").write_text(
                json.dumps(e, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        # 寫一份 selection manifest
        manifest = {
            "date": date,
            "selected_event_ids": [e["event_id"] for e in selected],
            "dropped": [
                {
                    "event_id": e["event_id"],
                    "headline": e.get("headline", ""),
                    "selection_score": e.get("selection_score", 0),
                    "drop_reason": e.get("drop_reason"),
                }
                for e in dropped
            ],
        }
        (events_dir / "_selection_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
