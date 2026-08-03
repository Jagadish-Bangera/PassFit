"""
core/dictionary_check.py

Offline common-password / dictionary check.
Spec ref: Section 3.5

Loads the precompiled Bloom filter (data/common_passwords.bloom) once and
checks the raw password AND its leetspeak-normalized form (from
core/pattern_detection.normalize_leetspeak) against it — so P@ssw0rd is
caught the same as password.

A match should immediately cap the strength score low, regardless of raw
entropy, per spec.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.bloom_filter import BloomFilter
from core.pattern_detection import normalize_leetspeak

_BLOOM_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "common_passwords.bloom")

_bloom_filter = None  # lazy-loaded singleton


def _get_filter() -> BloomFilter:
    global _bloom_filter
    if _bloom_filter is None:
        _bloom_filter = BloomFilter.load(_BLOOM_PATH)
    return _bloom_filter


def check_dictionary(password: str) -> dict:
    """
    Returns:
        {
            "is_common": bool,
            "matched_form": str | None,   # "raw" | "leetspeak-normalized" | None
        }
    """
    if not password:
        return {"is_common": False, "matched_form": None}

    bf = _get_filter()
    lowered = password.lower()

    if lowered in bf:
        return {"is_common": True, "matched_form": "raw"}

    normalized = normalize_leetspeak(lowered)
    if normalized != lowered and normalized in bf:
        return {"is_common": True, "matched_form": "leetspeak-normalized"}

    return {"is_common": False, "matched_form": None}


if __name__ == "__main__":
    samples = ["password", "PASSWORD", "P@ssw0rd", "correct-horse-battery-staple", "qwerty123!", "Xk9$mQ2vLp"]
    for pw in samples:
        result = check_dictionary(pw)
        print(f"{pw!r:35} -> {result}")
