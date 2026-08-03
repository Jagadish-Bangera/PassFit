"""
core/entropy.py

Entropy calculation for password strength analysis.
Spec ref: Section 3.2, Section 5 (Formulas Reference)

entropy_bits = length * log2(charset_size)
adjusted_entropy = entropy_bits - pattern_penalty

charset_size is the sum of character-class pool sizes ACTUALLY PRESENT
in the password (not the theoretical max the user could have used).
"""

import math
from dataclasses import dataclass

# Character class pool sizes, per spec Section 3.2
POOL_LOWER = 26
POOL_UPPER = 26
POOL_DIGIT = 10
POOL_SYMBOL = 32  # approx printable symbol set


@dataclass
class CharsetInfo:
    charset_size: int
    has_lower: bool
    has_upper: bool
    has_digit: bool
    has_symbol: bool


def analyze_charset(password: str) -> CharsetInfo:
    """Determine which character classes are present and the resulting pool size."""
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)

    charset_size = 0
    if has_lower:
        charset_size += POOL_LOWER
    if has_upper:
        charset_size += POOL_UPPER
    if has_digit:
        charset_size += POOL_DIGIT
    if has_symbol:
        charset_size += POOL_SYMBOL

    return CharsetInfo(
        charset_size=charset_size,
        has_lower=has_lower,
        has_upper=has_upper,
        has_digit=has_digit,
        has_symbol=has_symbol,
    )


def raw_entropy_bits(password: str) -> float:
    """
    Base formula: entropy = length * log2(charset_size)
    Returns 0.0 for an empty password (avoids log(0) domain error).
    """
    if not password:
        return 0.0

    info = analyze_charset(password)
    if info.charset_size == 0:
        return 0.0

    return len(password) * math.log2(info.charset_size)


def adjusted_entropy_bits(password: str, pattern_penalty_chars: int = 0) -> float:
    """
    Applies a pattern penalty to the raw entropy.

    pattern_penalty_chars: number of characters "consumed" by detected
    patterns (sequential runs, keyboard walks, repeats — see core/pattern_detection.py).
    We reduce the *effective length* used in the entropy formula by this
    amount before recomputing, per Section 5's guidance:
    "reduce effective length by the number of characters belonging to a
    detected pattern before computing entropy".

    Never returns a negative value.
    """
    if not password:
        return 0.0

    info = analyze_charset(password)
    if info.charset_size == 0:
        return 0.0

    effective_length = max(len(password) - pattern_penalty_chars, 0)
    if effective_length == 0:
        # Fully patterned password: treat as having a trivial 1-char floor
        # so the score isn't literally zero bits (still very low).
        effective_length = 1

    return effective_length * math.log2(info.charset_size)


def diversity_counts(password: str) -> dict:
    """
    Section 3.3 — live character diversity breakdown.
    Returns raw counts (not just presence) for each character class,
    so the UI can show e.g. "Digits: 4" not just a checkmark.
    """
    counts = {"upper": 0, "lower": 0, "digit": 0, "symbol": 0}
    for c in password:
        if c.isupper():
            counts["upper"] += 1
        elif c.islower():
            counts["lower"] += 1
        elif c.isdigit():
            counts["digit"] += 1
        elif not c.isspace():
            # Treat anything else printable as a symbol (matches
            # analyze_charset's "not alnum" symbol definition, minus whitespace)
            counts["symbol"] += 1
    return counts


def entropy_to_score_bucket(bits: float) -> str:
    """
    Maps adjusted entropy bits to a coarse strength bucket for the
    color-coded meter (Section 3.1: red -> orange -> yellow -> green).

    Thresholds are a reasonable starting point; tune later once the
    dictionary check (3.5) and crack-time models (3.6) exist, since a
    dictionary hit should be able to override this bucket downward.
    """
    if bits < 28:
        return "red"        # very weak — crackable in seconds/minutes
    elif bits < 36:
        return "orange"     # weak
    elif bits < 60:
        return "yellow"     # reasonable
    else:
        return "green"      # strong


if __name__ == "__main__":
    # Quick manual sanity checks
    samples = ["", "password", "P@ssw0rd", "Tr0ub4dor&3", "correct-horse-battery-staple"]
    for pw in samples:
        raw = raw_entropy_bits(pw)
        print(f"{pw!r:35} raw_entropy={raw:6.2f} bits  bucket={entropy_to_score_bucket(raw)}")