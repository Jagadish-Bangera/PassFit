"""
scripts/build_wordlist.py

One-time build step: raw wordlist -> compiled bundle.
Spec ref: Section 3.5 / 3.8, Section 6, Section 7 step 2.

Two modes:
    python scripts/build_wordlist.py dictionary <raw_wordlist.txt> [output_path]
        -> compiles a common-password list into a Bloom filter
           (data/common_passwords.bloom), for Section 3.5.

    python scripts/build_wordlist.py diceware <raw_wordlist.txt> [output_path]
        -> compiles a Diceware word list into a pickled index-accessible
           list (data/diceware_wordlist.bin), for Section 3.8. Unlike the
           dictionary check, passphrase generation needs to RETRIEVE actual
           words (not just test membership), so a Bloom filter doesn't fit
           here — a flat indexable list is the right structure, still
           compiled at build time rather than parsed as raw .txt at runtime.

Sources:
- Dictionary: SecLists' 10k-most-common.txt (https://github.com/danielmiessler/SecLists),
  a well-known, widely-used compilation of common/leaked passwords used for
  exactly this purpose (security tooling, not credential stuffing).
- Diceware: EFF's large wordlist (7,776 words = 6^5, genuine dice-roll math),
  the industry-standard wordlist for secure Diceware-style passphrases
  (https://www.eff.org/deeplinks/2016/07/new-wordlists-random-passphrases).
"""

import sys
import os
import pickle

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.bloom_filter import BloomFilter


def build_dictionary(wordlist_path: str, output_path: str, false_positive_rate: float = 0.000001):
    with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
        words = [line.strip().lower() for line in f if line.strip()]

    words = sorted(set(words))  # de-dupe
    print(f"Loaded {len(words)} unique words from {wordlist_path}")

    bf = BloomFilter.for_capacity(len(words), false_positive_rate=false_positive_rate)
    for w in words:
        bf.add(w)

    bf.save(output_path)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"Bloom filter built: size={bf.size} bits, k={bf.num_hashes} hashes")
    print(f"Saved to {output_path} ({size_kb:.1f} KB)")

    # Sanity check: every input word should test positive (no false negatives possible in a Bloom filter)
    missed = sum(1 for w in words if w not in bf)
    print(f"Sanity check: {missed} false negatives (should always be 0)")


def build_diceware(wordlist_path: str, output_path: str):
    """
    Parses the EFF large wordlist format (dice-roll number, tab, word) and
    compiles just the words into a pickled list for O(1) indexed access.
    """
    words = []
    with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 2:
                words.append(parts[1])
            elif len(parts) == 1 and parts[0]:
                # Fallback: plain one-word-per-line format, no dice-roll prefix
                words.append(parts[0])

    if not words:
        raise ValueError(f"No words parsed from {wordlist_path} — check the format.")

    with open(output_path, "wb") as f:
        pickle.dump(words, f, protocol=pickle.HIGHEST_PROTOCOL)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"Diceware list compiled: {len(words)} words")
    print(f"Saved to {output_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python scripts/build_wordlist.py dictionary <raw_wordlist.txt> [output_path]")
        print("  python scripts/build_wordlist.py diceware <raw_wordlist.txt> [output_path]")
        sys.exit(1)

    mode = sys.argv[1]
    wordlist_path = sys.argv[2]

    if mode == "dictionary":
        output_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
            os.path.dirname(__file__), "..", "data", "common_passwords.bloom"
        )
        build_dictionary(wordlist_path, output_path)
    elif mode == "diceware":
        output_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
            os.path.dirname(__file__), "..", "data", "diceware_wordlist.bin"
        )
        build_diceware(wordlist_path, output_path)
    else:
        print(f"Unknown mode: {mode!r}. Use 'dictionary' or 'diceware'.")
        sys.exit(1)