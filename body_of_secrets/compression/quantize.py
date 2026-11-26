"""Deterministic integer-frequency quantization for neural byte coding.

The quantizer reserves min_freq counts for every symbol, then distributes the
remaining budget proportionally with largest-remainder rounding.
"""
from __future__ import annotations

from numbers import Integral

import numpy as np


def quantize_cdf(
    probs: object,
    total: int = 4096,
    min_freq: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Quantize probabilities into positive integer frequencies and a CDF."""
    if not isinstance(total, Integral) or isinstance(total, (bool, np.bool_)):
        raise ValueError("total must be an integer")
    if not isinstance(min_freq, Integral) or isinstance(min_freq, (bool, np.bool_)):
        raise ValueError("min_freq must be an integer")
    total = int(total)
    min_freq = int(min_freq)
    if min_freq < 1:
        raise ValueError("min_freq must be at least 1")

    try:
        p = np.asarray(probs, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("probs must be a numeric one-dimensional array") from exc
    if p.ndim != 1 or p.size == 0:
        raise ValueError("probs must be a non-empty 1-D array")
    if not np.all(np.isfinite(p)):
        raise ValueError("probs must contain only finite values")
    if np.any(p < 0):
        raise ValueError("probs must be non-negative")

    n = int(p.size)
    if total < n * min_freq:
        raise ValueError("total must be >= n_symbols * min_freq")
    remaining = total - n * min_freq

    # Scale before summing to avoid overflow for large finite weights.
    peak = float(np.max(p))
    if peak == 0.0:
        normalized = np.full(n, 1.0 / n, dtype=np.float64)
    else:
        scaled = p / peak
        normalized = scaled / float(np.sum(scaled, dtype=np.float64))

    raw = normalized * remaining
    extra = np.floor(raw).astype(np.int64)
    unassigned = remaining - int(np.sum(extra, dtype=np.int64))
    if unassigned:
        fractions = raw - extra
        # Stable sort resolves ties by original (lowest) symbol index.
        order = np.argsort(-fractions, kind="stable")
        extra[order[:unassigned]] += 1

    freqs = extra + min_freq
    if int(np.sum(freqs, dtype=np.int64)) != total:
        raise AssertionError("frequency total mismatch")
    if np.any(freqs < min_freq):
        raise AssertionError("minimum frequency violated")

    cdf = np.empty(n + 1, dtype=np.int64)
    cdf[0] = 0
    np.cumsum(freqs, dtype=np.int64, out=cdf[1:])
    return freqs, cdf
