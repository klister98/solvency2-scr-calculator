"""Correlation aggregation: SCR = sqrt( sum_ij  Corr_ij * SCR_i * SCR_j )."""
import numpy as np


def aggregate(charges, corr) -> float:
    v = np.asarray(charges, dtype=float)
    c = np.asarray(corr, dtype=float)
    return float(np.sqrt(max(v @ c @ v, 0.0)))
