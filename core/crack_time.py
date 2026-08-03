"""
core/crack_time.py

Multi-model crack-time estimation.
Spec ref: Section 3.6, Section 5 (Formulas Reference)

Takes the ADJUSTED entropy (post pattern-penalty, post dictionary-cap —
i.e. whatever core.entropy.adjusted_entropy_bits() produced) and computes
estimated time-to-crack under three attack models, side by side, so the
person sees how much the hashing algorithm choice matters — not just
their password choice.

Formula (Section 5):
    total_combinations = 2 ^ adjusted_entropy_bits   (equivalent to charset_size ^ length,
                                                        but expressed directly in terms of
                                                        the entropy we already computed)
    seconds_to_crack   = total_combinations / hash_rate_per_second

Hash rate sourcing (updated from the spec's original ballpark figures to
current, citable benchmarks):

- Online (throttled): the spec's original "~100/sec" is barely throttled
  at all. A properly rate-limited login (lockout/CAPTCHA after N failed
  attempts) is modeled here using Dropbox's zxcvbn reference library's
  "online_throttling_100_per_hour" scenario (~0.0278/sec) — zxcvbn is the
  most widely cited password-strength model in security research and a
  defensible, named source for a synopsis.

- Offline fast hash (unsalted MD5/SHA1, GPU cracking): updated from the
  spec's "~10 billion/sec" to ~80 billion/sec, based on 2025 hashcat
  benchmarks showing a single RTX 4090 computing over 80,000 million
  MD5 hashes/sec (source: onlinehashcrack.com GPU benchmark report,
  2025). Kept as a single-GPU figure (conservative vs. multi-GPU rigs).

- Offline slow hash (bcrypt, cost factor 10): derived from a published
  RTX 4090 hashcat benchmark of ~180 kH/s for bcrypt at cost factor 5
  (source: tutorials.technology hashcat bcrypt benchmark table, 2026).
  Each bcrypt cost increment doubles the work, so cost 10 is 2^5 = 32x
  slower than cost 5: 180,000 / 32 ≈ 5,625/sec. This lands squarely
  inside the spec's original 1,000-10,000/sec range.
"""

from dataclasses import dataclass

# Section 3.6 attack model table
ATTACK_MODELS = [
    {
        "key": "online_throttled",
        "label": "Online (throttled)",
        "description": "Login/w/lockout,~100/hour",
        "hash_rate": 100 / 3600,  # zxcvbn: 100 attempts/hour
    },
    {
        "key": "offline_fast",
        "label": "Offline fast hash",
        "description": "Unsalted MD5/SHA1",
        "hash_rate": 80_000_000_000,  # ~80 billion/sec, 2025 RTX 4090 MD5 benchmark
    },
    {
        "key": "offline_slow",
        "label": "Offline slow hash",
        "description": "bcrypt cost 10",
        "hash_rate": 5_625,  # derived: 180 kH/s @ cost 5, /32 for cost 10
    },
]


@dataclass
class CrackTimeEstimate:
    key: str
    label: str
    description: str
    seconds: float
    human_readable: str


def seconds_to_human(seconds: float) -> str:
    """
    Converts a seconds value to the largest sensible unit, per Section 5:
    seconds -> minutes -> hours -> days -> years -> thousands/millions/
    billions of years.
    """
    if seconds < 1:
        return "instantly"

    minute, hour, day, year = 60, 3600, 86400, 31_557_600  # year = 365.25 days

    if seconds < minute:
        return f"{seconds:.0f} seconds"
    if seconds < hour:
        return f"{seconds / minute:.1f} minutes"
    if seconds < day:
        return f"{seconds / hour:.1f} hours"
    if seconds < year:
        return f"{seconds / day:.1f} days"

    years = seconds / year
    if years < 1_000:
        return f"{years:.1f} years"
    if years < 1_000_000:
        return f"{years / 1_000:.1f} thousand years"
    if years < 1_000_000_000:
        return f"{years / 1_000_000:.1f} million years"
    if years < 1_000_000_000_000:
        return f"{years / 1_000_000_000:.1f} billion years"
    if years < 1_000_000_000_000_000:
        return f"{years / 1_000_000_000_000:.1f} trillion years"
    # Beyond trillion, named units get absurd (quadrillion, quintillion...);
    # scientific notation stays readable at any magnitude.
    return f"{years:.2e} years"


def estimate_crack_times(adjusted_entropy_bits: float) -> list[CrackTimeEstimate]:
    """
    Returns one CrackTimeEstimate per attack model in ATTACK_MODELS, in
    the same order (online throttled -> offline fast -> offline slow),
    for side-by-side display.
    """
    total_combinations = 2 ** adjusted_entropy_bits

    results = []
    for model in ATTACK_MODELS:
        seconds = total_combinations / model["hash_rate"]
        results.append(
            CrackTimeEstimate(
                key=model["key"],
                label=model["label"],
                description=model["description"],
                seconds=seconds,
                human_readable=seconds_to_human(seconds),
            )
        )
    return results


if __name__ == "__main__":
    for bits in [10, 28, 36, 52.4, 60, 72.1, 118, 164]:
        print(f"\n--- {bits} bits ---")
        for est in estimate_crack_times(bits):
            print(f"  {est.label:22} {est.human_readable}")