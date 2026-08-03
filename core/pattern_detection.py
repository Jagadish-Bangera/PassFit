"""
core/pattern_detection.py

Pattern detection for password weaknesses.
Spec ref: Section 3.4

Detects and individually flags:
- Sequential runs (abcd, 1234, 4321)
- Keyboard walks (qwerty, asdfgh, 1qaz)
- Repeated characters / short repeated substrings (aaaa, abab)
- Leetspeak normalization (for the dictionary check in core/dictionary_check.py)

Each detected pattern marks the character positions it covers. The union
of all flagged positions becomes the "pattern_penalty_chars" count fed
into core.entropy.adjusted_entropy_bits(), per Section 5's guidance:
"reduce effective length by the number of characters belonging to a
detected pattern before computing entropy."
"""

import re
from dataclasses import dataclass


@dataclass
class Pattern:
    kind: str        # "sequential" | "keyboard_walk" | "repeated"
    text: str         # the exact matched substring, as it appears in the password
    start: int
    end: int          # exclusive

    def describe(self) -> str:
        labels = {
            "sequential": "Sequential run",
            "keyboard_walk": "Keyboard walk",
            "repeated": "Repeated characters",
        }
        kind_parts = self.kind.split("+")
        label = " + ".join(labels.get(k, k) for k in kind_parts)
        return f"{label}: {self.text}"


# ---------------------------------------------------------------------------
# 1. Sequential runs (ascending/descending, digits or letters)
# ---------------------------------------------------------------------------

def find_sequential_runs(password: str, min_length: int = 3) -> list[Pattern]:
    """
    Finds ascending or descending runs of consecutive digits or letters,
    e.g. 'abcd', '4321'. Case-insensitive for letters, but the matched
    text returned preserves the original casing from the password.
    """
    patterns = []
    n = len(password)
    i = 0
    while i < n - 1:
        c1, c2 = password[i], password[i + 1]
        if not (_same_class(c1, c2)):
            i += 1
            continue

        direction = _delta(c1, c2)
        if direction not in (1, -1):
            i += 1
            continue

        # Extend the run as far as it holds
        j = i + 1
        while j < n - 1 and _same_class(password[j], password[j + 1]) and _delta(password[j], password[j + 1]) == direction:
            j += 1

        run_len = j - i + 1
        if run_len >= min_length:
            patterns.append(Pattern("sequential", password[i:j + 1], i, j + 1))
            i = j + 1  # skip past this run, no overlap
        else:
            i += 1

    return patterns


def _same_class(c1: str, c2: str) -> bool:
    if c1.isdigit() and c2.isdigit():
        return True
    if c1.isalpha() and c2.isalpha():
        return True
    return False


def _delta(c1: str, c2: str):
    """Returns +1/-1 only if c2 is exactly one step after/before c1 (case-insensitive for letters), else None."""
    a = ord(c1.lower())
    b = ord(c2.lower())
    diff = b - a
    if diff == 1:
        return 1
    elif diff == -1:
        return -1
    return None


# ---------------------------------------------------------------------------
# 2. Keyboard walks (adjacent-key patterns, including diagonals like 1qaz)
# ---------------------------------------------------------------------------

_KEYBOARD_ROWS = [
    "1234567890",
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
]
# Approximate physical stagger offset per row (in "key width" units),
# modeled loosely on a real QWERTY keyboard so diagonal walks like
# '1qaz' / '2wsx' are detected as adjacent, not just same-row walks.
_ROW_OFFSETS = [0.0, 0.5, 0.75, 1.0]

_KEY_COORDS = {}
for _row_idx, _row in enumerate(_KEYBOARD_ROWS):
    for _col_idx, _ch in enumerate(_row):
        _KEY_COORDS[_ch] = (_row_idx, _col_idx + _ROW_OFFSETS[_row_idx])


def _key_delta(c1: str, c2: str):
    """
    Returns (d_row, d_x) if c1 and c2 are keyboard-adjacent (including
    diagonal neighbors on adjacent rows), else None.
    """
    a = _KEY_COORDS.get(c1.lower())
    b = _KEY_COORDS.get(c2.lower())
    if a is None or b is None:
        return None

    d_row = b[0] - a[0]
    d_x = b[1] - a[1]

    if d_row == 0 and abs(d_x) == 1:
        return (0, 1 if d_x > 0 else -1)
    if abs(d_row) == 1 and abs(d_x) <= 0.8:
        return (d_row, round(d_x, 2))
    return None


def find_keyboard_walks(password: str, min_length: int = 3) -> list[Pattern]:
    """
    Finds runs of consecutive keyboard-adjacent keys moving in a
    consistent direction, e.g. 'qwerty', 'asdfgh', '1qaz'.
    """
    patterns = []
    n = len(password)
    i = 0
    while i < n - 1:
        delta = _key_delta(password[i], password[i + 1])
        if delta is None:
            i += 1
            continue

        j = i + 1
        while j < n - 1 and _key_delta(password[j], password[j + 1]) == delta:
            j += 1

        run_len = j - i + 1
        if run_len >= min_length:
            patterns.append(Pattern("keyboard_walk", password[i:j + 1], i, j + 1))
            i = j + 1
        else:
            i += 1

    return patterns


# ---------------------------------------------------------------------------
# 3. Repeated characters / short repeated substrings
# ---------------------------------------------------------------------------

def find_repeated_patterns(password: str) -> list[Pattern]:
    """
    Finds two kinds of repetition:
    - 3+ consecutive repeats of the same character: 'aaaa'
    - A short substring (length 1-3) repeated back-to-back at least
      twice, covering 4+ characters total: 'abab', 'abcabc'
    """
    patterns = []
    n = len(password)
    flagged = [False] * n

    # 3+ repeats of the same character
    for match in re.finditer(r"(.)\1{2,}", password):
        start, end = match.start(), match.end()
        patterns.append(Pattern("repeated", password[start:end], start, end))
        for k in range(start, end):
            flagged[k] = True

    # Repeated short substrings (length 1-3), min 2 repeats, min 4 chars total,
    # skip positions already flagged by the single-char rule above.
    i = 0
    while i < n:
        if flagged[i]:
            i += 1
            continue
        matched = False
        for sub_len in (3, 2, 1):
            if i + sub_len * 2 > n:
                continue
            sub = password[i:i + sub_len]
            repeats = 1
            j = i + sub_len
            while password[j:j + sub_len] == sub and j + sub_len <= n:
                repeats += 1
                j += sub_len
            total_len = repeats * sub_len
            if repeats >= 2 and total_len >= 4 and not any(flagged[i:j]):
                patterns.append(Pattern("repeated", password[i:j], i, j))
                for k in range(i, j):
                    flagged[k] = True
                i = j
                matched = True
                break
        if not matched:
            i += 1

    return patterns


# ---------------------------------------------------------------------------
# 4. Leetspeak normalization (feeds into core/dictionary_check.py, Section 3.5)
# ---------------------------------------------------------------------------

_LEET_MAP = {
    "@": "a",
    "0": "o",
    "3": "e",
    "1": "i",
    "!": "i",
    "$": "s",
}


def normalize_leetspeak(password: str) -> str:
    """Replaces common leetspeak substitutions so dictionary checks catch e.g. P@ssw0rd -> Password."""
    return "".join(_LEET_MAP.get(c, c) for c in password)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def detect_all_patterns(password: str) -> list[Pattern]:
    """
    Runs all detectors and returns a de-duplicated, position-sorted list.
    When two detectors flag the exact same character range (e.g. '1234'
    is both a sequential run and a keyboard walk), those are merged into
    a single Pattern with a combined label — showing '1234' twice as two
    separate lines reads as redundant noise, even though both facts are
    individually true.
    """
    patterns = []
    patterns.extend(find_sequential_runs(password))
    patterns.extend(find_keyboard_walks(password))
    patterns.extend(find_repeated_patterns(password))
    patterns.sort(key=lambda p: p.start)

    merged = []
    seen_ranges = {}  # (start, end) -> index into merged
    for p in patterns:
        key = (p.start, p.end)
        if key in seen_ranges:
            existing = merged[seen_ranges[key]]
            if p.kind not in existing.kind.split("+"):
                existing.kind = existing.kind + "+" + p.kind
        else:
            seen_ranges[key] = len(merged)
            merged.append(p)

    return merged


def feedback_lines(patterns: list[Pattern], max_lines: int = 5) -> list[str]:
    """
    Human-readable feedback lines, capped so the UI doesn't get flooded
    when a password has many distinct weak substrings. Excess matches
    are summarized in a trailing "+N more" line instead of listed out.
    """
    lines = [p.describe() for p in patterns]
    if len(lines) <= max_lines:
        return lines
    shown = lines[:max_lines]
    shown.append(f"+ {len(lines) - max_lines} more pattern(s) detected")
    return shown


def pattern_penalty_chars(password: str, patterns: list[Pattern] = None) -> int:
    """
    Returns the count of unique character positions covered by any
    detected pattern — this is what gets subtracted from effective
    length in core.entropy.adjusted_entropy_bits().
    """
    if patterns is None:
        patterns = detect_all_patterns(password)

    flagged = [False] * len(password)
    for p in patterns:
        for k in range(p.start, p.end):
            flagged[k] = True
    return sum(flagged)


if __name__ == "__main__":
    samples = ["qwerty123!", "P@ssw0rd", "aaaa", "abab", "correct-horse-battery-staple", "Tr0ub4dor&3"]
    for pw in samples:
        pats = detect_all_patterns(pw)
        penalty = pattern_penalty_chars(pw, pats)
        print(f"\n{pw!r} -> penalty_chars={penalty}")
        for p in pats:
            print(f"   {p.describe()}  (pos {p.start}:{p.end})")
        print(f"   leetspeak-normalized: {normalize_leetspeak(pw)!r}")