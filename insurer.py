"""The synthetic insurer: loads the data and builds the Solvency II balance sheet."""
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import assets as A
import curve as C
import liabilities as L

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


@dataclass
class Insurer:
    term: pd.DataFrame
    annuities: pd.DataFrame
    bonds: pd.DataFrame
    other: A.OtherAssets = field(default_factory=A.OtherAssets)
    risk_margin: float = 18_000_000      # input in v1 (not recalculated under shocks)
    curve: np.ndarray = field(default_factory=C.base_curve)
    symmetric_adjustment: float = 0.0

    @classmethod
    def load(cls, **kwargs):
        return cls(
            term=pd.read_csv(os.path.join(DATA, "term_policies.csv")),
            annuities=pd.read_csv(os.path.join(DATA, "annuities.csv")),
            bonds=pd.read_csv(os.path.join(DATA, "bonds.csv")),
            **kwargs,
        )

    # ---- liabilities -------------------------------------------------------
    def bel(self, basis: L.Basis = L.BEST_ESTIMATE, curve: np.ndarray = None) -> dict:
        curve = self.curve if curve is None else curve
        cf = L.project(self.term, self.annuities, basis)
        return L.bel(cf, C.discount_factors(curve, len(cf["term"]) - 1))

    # ---- assets ------------------------------------------------------------
    def bond_table(self, curve: np.ndarray = None) -> pd.DataFrame:
        return A.value_bonds(self.bonds, self.curve if curve is None else curve)

    def total_assets(self, curve: np.ndarray = None) -> float:
        o = self.other
        bonds = self.bond_table(curve)["market_value"].sum()
        return float(bonds + o.equity_type1 + o.equity_type2 + o.property + o.cash
                     + o.receivables_current + o.receivables_overdue)

    # ---- balance sheet -----------------------------------------------------
    def balance_sheet(self) -> dict:
        b = self.bel()
        total_assets = self.total_assets()
        tp = b["total"] + self.risk_margin
        return {
            "assets": total_assets,
            "bel_term": b["term"],
            "bel_annuity": b["annuity"],
            "bel": b["total"],
            "risk_margin": self.risk_margin,
            "technical_provisions": tp,
            "own_funds": total_assets - tp,   # all assumed Tier 1 in v1
        }
