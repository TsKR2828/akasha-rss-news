"""Named Entity Recognition for beat classification.

Uses spaCy NER to extract entities and score them against beat-specific
entity patterns.  This provides the 0.1 entity_weight in the §6.1 formula:

    score = 0.6 * source_default + 0.3 * keyword + 0.1 * entity

Graceful degradation: if spaCy or the language model is not installed,
all entity scores default to 0.0 (equivalent to prior MVP behaviour).
"""
from __future__ import annotations

import logging

LOG = logging.getLogger(__name__)

_nlp = None
_nlp_load_attempted = False


# ---------------------------------------------------------------------------
# Model loading (lazy, one-shot)
# ---------------------------------------------------------------------------

def _load_nlp():
    """Lazy-load spaCy ``en_core_web_sm``.  Returns *None* if unavailable."""
    global _nlp, _nlp_load_attempted
    if _nlp_load_attempted:
        return _nlp
    _nlp_load_attempted = True
    try:
        import spacy  # noqa: F811
        _nlp = spacy.load("en_core_web_sm")
        LOG.info("spaCy model 'en_core_web_sm' loaded")
    except ImportError:
        LOG.warning("spaCy not installed; entity scoring disabled (score=0)")
    except OSError:
        LOG.warning(
            "spaCy model 'en_core_web_sm' not found; "
            "run: python -m spacy download en_core_web_sm"
        )
    return _nlp


def reset() -> None:
    """Reset cached model — for testing only."""
    global _nlp, _nlp_load_attempted
    _nlp = None
    _nlp_load_attempted = False


# ---------------------------------------------------------------------------
# Entity extraction
# ---------------------------------------------------------------------------

def extract_entities(text: str) -> list[dict]:
    """Extract named entities from *text* via spaCy.

    Returns
    -------
    list[dict]
        Each dict has ``{"text": str, "label": str}``.
        Empty list when spaCy is unavailable or *text* is empty.
    """
    if not text:
        return []
    nlp = _load_nlp()
    if nlp is None:
        return []
    # Cap input length to keep inference fast on long articles
    doc = nlp(text[:10_000])
    return [{"text": ent.text, "label": ent.label_} for ent in doc.ents]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def entity_match_score(
    entities: list[dict],
    beat_entity_config: dict,
) -> float:
    """Score entity matches for one beat.

    Uses the same scale as ``keyword_match_score``:

    * **≥ 2 hits** → 1.0
    * **1 hit**    → 0.5
    * **0 hits**   → 0.0

    A *hit* is either:

    * entity text matches an entry in ``entity_names`` (case-insensitive), or
    * entity label matches an entry in ``entity_types`` (exact).

    Each unique ``(text.lower(), label)`` pair counts at most once.
    """
    if not entities or not beat_entity_config:
        return 0.0

    names = {n.lower() for n in beat_entity_config.get("entity_names", [])}
    types = set(beat_entity_config.get("entity_types", []))

    hits = 0
    seen: set[tuple[str, str]] = set()

    for ent in entities:
        key = (ent["text"].lower(), ent["label"])
        if key in seen:
            continue
        seen.add(key)

        if ent["text"].lower() in names:
            hits += 1
        elif ent["label"] in types:
            hits += 1

    if hits >= 2:
        return 1.0
    if hits == 1:
        return 0.5
    return 0.0
