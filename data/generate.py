"""
Generate the synthetic insurer used by the calculator.

Run from the project folder:  python data/generate.py
Creates term_policies.csv, annuities.csv and bonds.csv in data/.
Everything is invented; the random seed makes it reproducible.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mortality  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(2026)

# ---------------- term assurance ----------------
N_TERM = 10_000
PRICING_RATE = 0.03
PRICING_LAPSE = 0.06
PRICING_LOADING = 1.30   # premium = 130% of expected claims + expenses

ages = rng.integers(25, 56, N_TERM)
terms = rng.choice([10, 15, 20, 25, 30], N_TERM)
terms = np.minimum(terms, 65 - ages)            # cover ends by age 65
sums = rng.choice([50_000, 100_000, 150_000, 250_000, 500_000], N_TERM, p=[0.2, 0.3, 0.2, 0.2, 0.1])
expense = np.full(N_TERM, 60.0)

pv_claims = np.zeros(N_TERM)
pv_exp = np.zeros(N_TERM)
pv_prem_annuity = np.zeros(N_TERM)
inforce = np.ones(N_TERM)
for t in range(int(terms.max())):
    active = t < terms
    q = mortality.qx(ages + t)
    v_start = (1 + PRICING_RATE) ** -t
    v_end = (1 + PRICING_RATE) ** -(t + 1)
    pv_prem_annuity += active * inforce * v_start
    pv_exp += active * inforce * expense * 1.02 ** t * v_start
    pv_claims += active * inforce * q * sums * v_end
    inforce = inforce * (1 - q) * (1 - PRICING_LAPSE)
premium = PRICING_LOADING * (pv_claims + pv_exp) / pv_prem_annuity

term = pd.DataFrame({
    "policy_id": np.arange(1, N_TERM + 1),
    "age": ages, "term": terms, "sum_assured": sums,
    "annual_premium": premium.round(2), "annual_expense": expense,
})

# ---------------- immediate annuities ----------------
N_ANN = 2_000
ann = pd.DataFrame({
    "annuitant_id": np.arange(1, N_ANN + 1),
    "age": rng.integers(60, 81, N_ANN),
    "annual_annuity": rng.choice([6_000, 10_000, 15_000, 20_000, 30_000], N_ANN, p=[0.25, 0.3, 0.25, 0.15, 0.05]),
    "annual_expense": np.full(N_ANN, 40.0),
})

# ---------------- bond portfolio ----------------
# type: govt (EEA sovereign, no spread charge) or corp; cqs = credit quality step (0 = AAA)
bonds = pd.DataFrame([
    # name,              type,   cqs, notional,     coupon, maturity, spread over risk-free
    ("Govt 2031",        "govt", 0,  60_000_000,   0.025,  5,  0.000),
    ("Govt 2036",        "govt", 0,  60_000_000,   0.030,  10, 0.000),
    ("Govt 2046",        "govt", 0,  70_000_000,   0.033,  20, 0.000),
    ("Govt 2056",        "govt", 0,  30_000_000,   0.035,  30, 0.000),
    ("Corp AA 2033",     "corp", 1,  45_000_000,   0.034,  7,  0.008),
    ("Corp A 2036",      "corp", 2,  50_000_000,   0.038,  10, 0.012),
    ("Corp A 2041",      "corp", 2,  30_000_000,   0.040,  15, 0.014),
    ("Corp BBB 2034",    "corp", 3,  30_000_000,   0.045,  8,  0.020),
], columns=["name", "type", "cqs", "notional", "coupon", "maturity", "spread"])

term.to_csv(os.path.join(HERE, "term_policies.csv"), index=False)
ann.to_csv(os.path.join(HERE, "annuities.csv"), index=False)
bonds.to_csv(os.path.join(HERE, "bonds.csv"), index=False)
print(f"term policies: {len(term):,}  annuitants: {len(ann):,}  bonds: {len(bonds)}")
print(f"total sum assured: {term.sum_assured.sum():,.0f}  annual annuity: {ann.annual_annuity.sum():,.0f}")
