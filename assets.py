"""Asset side: bond valuation on the risk-free curve plus a spread, and the other asset classes."""
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class OtherAssets:
    """Asset classes valued at market value (EUR). Edit these to change the asset mix."""
    equity_type1: float = 30_000_000
    equity_type2: float = 10_000_000
    property: float = 15_000_000
    cash: float = 15_000_000
    receivables_current: float = 4_000_000          # premiums due from intermediaries, < 3 months
    receivables_overdue: float = 500_000            # due from intermediaries, > 3 months overdue


def bond_cashflows(row) -> np.ndarray:
    """Annual coupons and redemption, index = time in years."""
    n = int(row["maturity"])
    cf = np.zeros(n + 1)
    cf[1:] = row["notional"] * row["coupon"]
    cf[n] += row["notional"]
    return cf


def bond_value(row, curve: np.ndarray, extra_spread: float = 0.0) -> float:
    """Market value = cash flows discounted at risk-free + the bond's spread."""
    cf = bond_cashflows(row)
    t = np.arange(len(cf))
    rates = curve[: len(cf)] + row["spread"] + extra_spread
    return float(np.sum(cf * (1 + rates) ** (-t.astype(float))))


def modified_duration(row, curve: np.ndarray, bump: float = 0.0001) -> float:
    """Effective (modified) duration from a small parallel bump."""
    up = bond_value(row, curve, bump)
    down = bond_value(row, curve, -bump)
    base = bond_value(row, curve)
    return (down - up) / (2 * bump * base)


def value_bonds(bonds: pd.DataFrame, curve: np.ndarray) -> pd.DataFrame:
    out = bonds.copy()
    out["market_value"] = [bond_value(r, curve) for _, r in bonds.iterrows()]
    out["duration"] = [modified_duration(r, curve) for _, r in bonds.iterrows()]
    return out
