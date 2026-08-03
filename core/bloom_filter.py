"""
core/bloom_filter.py

A minimal, dependency-free Bloom filter.

Why hand-roll this instead of pip-installing one: keeps the final PyInstaller
.exe lean and avoids an extra third-party dependency for something this small.
Uses double hashing (two independent hash functions combined) to simulate
k hash functions without needing k separate hash computations — a standard
technique for Bloom filter implementations.

Spec ref: Section 2 (Tech Stack — "Bloom filter or precomputed set at build
time"), Section 3.5, Section 9 ("keep binary size reasonable").
"""

import hashlib
import math
import pickle


class BloomFilter:
    def __init__(self, size: int, num_hashes: int):
        self.size = size
        self.num_hashes = num_hashes
        self.bit_array = bytearray((size + 7) // 8)

    @classmethod
    def for_capacity(cls, n_items: int, false_positive_rate: float = 0.01):
        """
        Sizes a new, empty Bloom filter for n_items with the given target
        false-positive rate, using standard Bloom filter sizing formulas:
            m = -(n * ln(p)) / (ln 2)^2
            k = (m / n) * ln 2
        """
        m = math.ceil(-(n_items * math.log(false_positive_rate)) / (math.log(2) ** 2))
        k = max(1, round((m / n_items) * math.log(2)))
        return cls(size=m, num_hashes=k)

    def _bit_indices(self, item: str):
        # Two independent hashes, combined via double hashing to derive
        # num_hashes distinct index positions without k separate digests.
        h1 = int(hashlib.sha256(item.encode("utf-8")).hexdigest(), 16)
        h2 = int(hashlib.md5(item.encode("utf-8")).hexdigest(), 16)
        for i in range(self.num_hashes):
            yield (h1 + i * h2) % self.size

    def add(self, item: str):
        for idx in self._bit_indices(item):
            self.bit_array[idx // 8] |= (1 << (idx % 8))

    def __contains__(self, item: str) -> bool:
        return all(
            self.bit_array[idx // 8] & (1 << (idx % 8))
            for idx in self._bit_indices(item)
        )

    def save(self, path: str):
        with open(path, "wb") as f:
            pickle.dump(
                {"size": self.size, "num_hashes": self.num_hashes, "bits": bytes(self.bit_array)},
                f,
                protocol=pickle.HIGHEST_PROTOCOL,
            )

    @classmethod
    def load(cls, path: str) -> "BloomFilter":
        with open(path, "rb") as f:
            data = pickle.load(f)
        bf = cls(size=data["size"], num_hashes=data["num_hashes"])
        bf.bit_array = bytearray(data["bits"])
        return bf
