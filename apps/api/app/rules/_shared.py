"""
Shared text-matching utilities for the rule engine.

Used by step2_diagnosis.py, step5_insurer.py, and any future rule steps
so that normalization and keyword-matching behaviour stays consistent across
the entire pipeline.  Import from here; do not re-implement inline.
"""

import re

# Pre-compiled once at import time — shared across all callers.
_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]+")


# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

def normalize_text(value: str) -> str:
    """Lowercase, strip non-alphanumeric characters, collapse whitespace.

    Example::
        normalize_text("IV-Cannula (18G)") == "iv cannula 18g"
    """
    text = _NON_ALNUM_RE.sub(" ", value.lower())
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# Token-safe phrase matching
# ---------------------------------------------------------------------------

def contains_phrase(haystack: str, needle: str) -> bool:
    """Return True when *needle* appears as a complete phrase inside *haystack*.

    Pads both strings with a leading and trailing space so that a keyword
    like ``"cap"`` does **not** match ``"capsule"``, ``"escape"``, etc.

    Both arguments are expected to already be normalised (lowercase, stripped).
    """
    if not haystack or not needle:
        return False
    return f" {needle} " in f" {haystack} "


# ---------------------------------------------------------------------------
# Multi-keyword item matching
# ---------------------------------------------------------------------------

def keyword_matches_item(
    desc_norm: str,
    keywords: list[str],
) -> tuple[bool, str | None]:
    """Check whether any keyword in *keywords* phrase-matches *desc_norm*.

    Returns ``(True, matched_keyword)`` on the first match, or
    ``(False, None)`` when nothing matches.

    *desc_norm* should already be normalised via :func:`normalize_text`.
    Each keyword is normalised inside this function so callers do not need
    to pre-process them.
    """
    for kw in keywords:
        kw_norm = normalize_text(kw)
        if contains_phrase(desc_norm, kw_norm):
            return True, kw
    return False, None


# ---------------------------------------------------------------------------
# Category helpers
# ---------------------------------------------------------------------------

def is_unclassified(category: str | None) -> bool:
    """Return True when *category* represents an absent or unknown category.

    Treats ``None``, empty string, and the sentinel value ``"UNCLASSIFIED"``
    as equivalent so callers don't need to repeat this trio.
    """
    return not category or category == "UNCLASSIFIED"
