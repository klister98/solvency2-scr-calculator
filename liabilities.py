"""
Liability projection and best estimate liability (BEL).

Two blocks of business:
  * term assurance  - premiums in, death claims out (mortality and lapse risk)
  * immediate annuities - annual payments while alive (longevity risk)

Every life shock is applied by changing an assumption in `Basis` and re-running
the projection. Annual time steps; premiums and expenses at the start of each
year, claims, annuity payments and lapses at the end.
"""
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

import mortality

ANNUITANT_MORTALITY_MULT = 0.75   # annuitants live longer than the general population
MAX_AGE = 110


@dataclass(frozen=True)
class Basis:
    """Best estimate assumptions. Shocks are applied with `dataclasses.replace`."""
    mortality_mult: float = 1.0        # scales mortality rates (term block)
    annuity_mortality_mult: float = 1.0  # scales mortality rates (annuity block)
    lapse_rate: float = 0.06           # annual lapse rate, term block
    mass_lapse: float = 0.0            # share of term policies lapsing immediately
    expense_mult: float = 1.0          # scales per-policy expenses
    expense_inflation: float = 0.02
    cat_addition: float = 0.0          # extra death probability in year 1 (term block)


BEST_ESTIMATE = Basis()


def _term_cashflows(policies: pd.DataFrame, basis: Basis, horizon: int):
    """Net outgo by year (index = time of cash flow, 0..horizon) for the term block."""
    n = len(policies)
    ages = policies["age"].to_numpy()
    terms = policies["term"].to_numpy()
    sa = policies["sum_assured"].to_numpy()
    prem = policies["annual_premium"].to_numpy()
    exp0 = policies["annual_expense"].to_numpy()

    inforce = np.full(n, 1.0 - basis.mass_lapse)
    net = np.zeros(horizon + 1)
    for t in range(horizon):
        active = t < terms
        if not active.any():
            break
        q = mortality.qx(ages + t, basis.mortality_mult)
        if t == 0:
            q = np.minimum(q + basis.cat_addition, 1.0)
        live = inforce * active
        expense = exp0 * basis.expense_mult * (1 + basis.expense_inflation) ** t
        net[t] += np.sum(live * (expense - prem))          # start of year: expenses out, premiums in
        net[t + 1] += np.sum(live * q * sa)               # end of year: death claims
        inforce = inforce * (1 - q) * (1 - basis.lapse_rate)
    return net


def _annuity_cashflows(annuitants: pd.DataFrame, basis: Basis, horizon: int):
    """Net outgo by year for the annuity block (payments in arrears, expenses in advance)."""
    ages = annuitants["age"].to_numpy()
    amount = annuitants["annual_annuity"].to_numpy()
    exp0 = annuitants["annual_expense"].to_numpy()
    mult = ANNUITANT_MORTALITY_MULT * basis.annuity_mortality_mult

    alive = np.ones(len(annuitants))
    net = np.zeros(horizon + 1)
    for t in range(horizon):
        if (ages + t >= MAX_AGE).all():
            break
        q = mortality.qx(ages + t, mult)
        q = np.where(ages + t >= MAX_AGE, 1.0, q)
        expense = exp0 * basis.expense_mult * (1 + basis.expense_inflation) ** t
        net[t] += np.sum(alive * expense)
        survivors = alive * (1 - q)
        net[t + 1] += np.sum(survivors * amount)
        alive = survivors
    return net


def project(term: pd.DataFrame, annuities: pd.DataFrame, basis: Basis = BEST_ESTIMATE, horizon: int = 60):
    """Return net outgo cash flows (positive = money paid out) for each block."""
    return {
        "term": _term_cashflows(term, basis, horizon),
        "annuity": _annuity_cashflows(annuities, basis, horizon),
    }


def bel(cashflows: dict, discount: np.ndarray) -> dict:
    """Present value of net outgo for each block, plus the total."""
    out = {k: float(np.dot(v, discount[: len(v)])) for k, v in cashflows.items()}
    out["total"] = out["term"] + out["annuity"]
    return out


def shocked(basis: Basis = BEST_ESTIMATE, **changes) -> Basis:
    return replace(basis, **changes)
