"""Synthetic mortality basis (Gompertz-Makeham), roughly in line with a European population table."""
import numpy as np

A, B, C = 0.00022, 0.0000027, 1.124


def qx(ages, multiplier: float = 1.0) -> np.ndarray:
    """One-year death probabilities at the given ages, scaled by `multiplier`, capped at 1."""
    ages = np.asarray(ages, dtype=float)
    mu = A + B * C ** ages
    q = 1 - np.exp(-mu)
    return np.clip(q * multiplier, 0.0, 1.0)
