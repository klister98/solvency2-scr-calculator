"""Risk-free curve, interest rate shocks and discount factors."""
import numpy as np

import params

MAX_T = 120  # years of curve we keep


def base_curve(level_shift: float = 0.0) -> np.ndarray:
    """Synthetic risk-free spot curve: ~2.6% at 1 year rising to ~3.7% long-term.

    Index t holds the annual spot rate for maturity t years (index 0 unused).
    `level_shift` moves the whole curve (used for the 'rates -100bp' scenario).
    """
    t = np.arange(MAX_T + 1)
    r = 0.025 + 0.012 * (1 - np.exp(-t / 8.0)) + level_shift
    r[0] = r[1]
    return r


def _shock_factor(table: dict, maturity: int) -> float:
    """Relative shock for a maturity: table values to 20y, linear to 90y, flat after."""
    if maturity <= 1:
        return table[1]
    if maturity <= 20:
        return table[maturity]
    if maturity >= 90:
        return table[90]
    w = (maturity - 20) / (90 - 20)
    return table[20] + w * (table[90] - table[20])


def shocked_curve(curve: np.ndarray, direction: str) -> np.ndarray:
    """Apply the standard formula up or down shock (Arts. 166-167, 2015 calibration)."""
    out = curve.copy()
    for m in range(1, len(curve)):
        r = curve[m]
        if direction == "up":
            s = _shock_factor(params.IR_UP_SHOCK, m)
            out[m] = max(r * (1 + s), r + params.IR_UP_MIN_ABS_INCREASE)
        elif direction == "down":
            s = _shock_factor(params.IR_DOWN_SHOCK, m)
            out[m] = r * (1 - s) if r > 0 else r   # negative rates are not shocked down
        else:
            raise ValueError(direction)
    out[0] = out[1]
    return out


def discount_factors(curve: np.ndarray, n: int) -> np.ndarray:
    """Discount factors for cash flows at times 0..n (DF(0) = 1)."""
    t = np.arange(n + 1)
    return (1 + curve[: n + 1]) ** (-t.astype(float))
