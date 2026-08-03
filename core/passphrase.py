"""
core/passphrase.py

Diceware-style passphrase generator.
Spec ref: Section 3.8

Uses the same `secrets` module (never `random`) as core/generator.py.
Words come from the compiled EFF large wordlist (data/diceware_wordlist.bin,
built by scripts/build_wordlist.py diceware mode) — never parsed from raw
.txt at runtime, consistent with Section 3.5's approach.
"""

import os
import secrets
import pickle

_WORDLIST_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "diceware_wordlist.bin")

_wordlist = None  # lazy-loaded singleton


def _get_wordlist() -> list:
    global _wordlist
    if _wordlist is None:
        with open(_WORDLIST_PATH, "rb") as f:
            _wordlist = pickle.load(f)
    return _wordlist


def generate_passphrase(word_count: int = 5, separator: str = "-", capitalize: bool = False) -> str:
    """
    Generates a Diceware-style passphrase, e.g. 'correct-horse-battery-staple'.

    word_count: number of words (spec default range: 4-6)
    separator: joining character between words
    capitalize: if True, capitalizes the first letter of each word
    """
    if word_count < 1:
        raise ValueError("word_count must be at least 1")

    wordlist = _get_wordlist()
    words = [secrets.choice(wordlist) for _ in range(word_count)]

    if capitalize:
        words = [w.capitalize() for w in words]

    return separator.join(words)


def wordlist_size() -> int:
    """Number of words available — useful for entropy-per-word documentation (log2(7776) ≈ 12.9 bits/word)."""
    return len(_get_wordlist())


def passphrase_entropy_bits(word_count: int) -> float:
    """
    True entropy of a Diceware-style passphrase: word_count * log2(wordlist_size).
    This is the CORRECT way to measure it — NOT length * log2(charset_size)
    (the formula used elsewhere in this app for regular passwords). A
    character-based formula treats each letter as independently random,
    wildly overstating security here: a real attacker who recognizes a
    passphrase pattern runs a wordlist-combinator attack against the
    actual ~7,776-word search space per word, not full character brute
    force. This is the same "naive entropy overstates strength" problem
    the whole app is designed to catch elsewhere (Section 3.2) — it just
    also applies to the app's own passphrase feature.
    """
    import math
    return word_count * math.log2(wordlist_size())


if __name__ == "__main__":
    import math

    print(f"Wordlist size: {wordlist_size()} words (~{math.log2(wordlist_size()):.2f} bits/word)")
    for n in (4, 5, 6):
        print(f"{n} words: {generate_passphrase(n)}")
    print("Capitalized:", generate_passphrase(4, capitalize=True))
    print("Custom separator:", generate_passphrase(5, separator=" "))