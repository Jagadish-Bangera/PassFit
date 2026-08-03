"""
core/generator.py

Cryptographically secure password generator.
Spec ref: Section 3.7

Uses Python's `secrets` module exclusively — NEVER `random` — since this
output is meant to actually be used as a real password, not just a demo.
"""

import secrets
import string

LOWER = string.ascii_lowercase
UPPER = string.ascii_uppercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?"


def generate_password(
    length: int = 16,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
) -> str:
    """
    Generates a cryptographically random password of the given length,
    drawing from the enabled character classes. Guarantees at least one
    character from each *enabled* class (when length allows), so a short
    password can't accidentally end up missing a whole requested class.

    Raises ValueError if no character class is enabled, or if length is
    too short to include one of each enabled class.
    """
    pools = []
    if use_upper:
        pools.append(UPPER)
    if use_lower:
        pools.append(LOWER)
    if use_digits:
        pools.append(DIGITS)
    if use_symbols:
        pools.append(SYMBOLS)

    if not pools:
        raise ValueError("At least one character class must be enabled.")
    if length < len(pools):
        raise ValueError(f"Length must be at least {len(pools)} to include every enabled character class.")

    # Guarantee one char from each enabled pool, per Section 3.7 intent
    # (generated password should reliably satisfy its own toggles).
    required = [secrets.choice(pool) for pool in pools]

    combined = "".join(pools)
    remaining = [secrets.choice(combined) for _ in range(length - len(required))]

    all_chars = required + remaining

    # Shuffle using secrets (Fisher-Yates), NOT random.shuffle
    for i in range(len(all_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        all_chars[i], all_chars[j] = all_chars[j], all_chars[i]

    return "".join(all_chars)


if __name__ == "__main__":
    for _ in range(5):
        print(generate_password(16))
    print(generate_password(8, use_symbols=False))
    print(generate_password(24))