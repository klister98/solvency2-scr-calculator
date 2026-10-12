"""
Standard formula parameters used by the calculator.

Every value carries the article of Commission Delegated Regulation (EU) 2015/35
(as amended) it comes from. The values were entered from memory of the
regulation and MUST be checked against the official consolidated text on
EUR-Lex before the results are relied on. Items marked "VERIFY" are the ones
most likely to have changed through later amendments (2019 review and the
2024/2025 Solvency II review, which recalibrates interest rate risk with a
phase-in and changes the risk margin cost of capital from 2027).
"""

# ---------------------------------------------------------------------------
# Market risk
# ---------------------------------------------------------------------------

# Equity risk (Art. 169)
EQUITY_SHOCK_TYPE1 = 0.39          # listed in EEA / OECD regulated markets
EQUITY_SHOCK_TYPE2 = 0.49          # unlisted, private equity, hedge funds, other
EQUITY_SHOCK_STRATEGIC = 0.22      # strategic participations (Art. 171) - not used in v1
EQUITY_TYPE1_TYPE2_CORR = 0.75     # Art. 168(7)

# Symmetric adjustment (Art. 172): published monthly by EIOPA, bounded at +/-10%.
SYMMETRIC_ADJUSTMENT = 0.0         # input; set to the current EIOPA value
SA_BOUNDS = (-0.10, 0.10)

# Property risk (Art. 174)
PROPERTY_SHOCK = 0.25

# Interest rate risk (Arts. 166-167) - relative shocks to the risk-free curve
# by maturity in years. These are the ORIGINAL 2015 values. VERIFY: the
# 2024/2025 review introduces a new calibration (relative + absolute shift,
# phased in), which would replace these tables.
IR_UP_SHOCK = {
    1: 0.70, 2: 0.70, 3: 0.64, 4: 0.59, 5: 0.55, 6: 0.52, 7: 0.49, 8: 0.47,
    9: 0.44, 10: 0.42, 11: 0.39, 12: 0.37, 13: 0.35, 14: 0.34, 15: 0.33,
    16: 0.31, 17: 0.30, 18: 0.29, 19: 0.27, 20: 0.26, 90: 0.20,
}
IR_DOWN_SHOCK = {
    1: 0.75, 2: 0.65, 3: 0.56, 4: 0.50, 5: 0.46, 6: 0.42, 7: 0.39, 8: 0.36,
    9: 0.33, 10: 0.31, 11: 0.30, 12: 0.29, 13: 0.28, 14: 0.28, 15: 0.27,
    16: 0.28, 17: 0.28, 18: 0.28, 19: 0.29, 20: 0.29, 90: 0.20,
}
IR_UP_MIN_ABS_INCREASE = 0.01      # the up shock adds at least 1 percentage point

# Spread risk on bonds (Art. 176) - stress = a + b * (duration - lower bound),
# by credit quality step (CQS 0 = AAA ... 6 = CCC or lower). VERIFY all bands.
# Each row: (upper duration bound, a, b, lower duration bound)
SPREAD_FACTORS = {
    0: [(5, 0.000, 0.009, 0), (10, 0.045, 0.005, 5), (15, 0.070, 0.005, 10), (20, 0.095, 0.005, 15), (999, 0.120, 0.005, 20)],
    1: [(5, 0.000, 0.011, 0), (10, 0.055, 0.006, 5), (15, 0.085, 0.005, 10), (20, 0.110, 0.005, 15), (999, 0.135, 0.005, 20)],
    2: [(5, 0.000, 0.014, 0), (10, 0.070, 0.007, 5), (15, 0.105, 0.005, 10), (20, 0.130, 0.005, 15), (999, 0.155, 0.005, 20)],
    3: [(5, 0.000, 0.025, 0), (10, 0.125, 0.015, 5), (15, 0.200, 0.010, 10), (20, 0.250, 0.010, 15), (999, 0.300, 0.005, 20)],
    4: [(5, 0.000, 0.045, 0), (10, 0.225, 0.025, 5), (15, 0.350, 0.018, 10), (20, 0.440, 0.005, 15), (999, 0.465, 0.005, 20)],
    5: [(5, 0.000, 0.075, 0), (10, 0.375, 0.042, 5), (15, 0.585, 0.005, 10), (20, 0.610, 0.005, 15), (999, 0.635, 0.005, 20)],
    6: [(5, 0.000, 0.075, 0), (10, 0.375, 0.042, 5), (15, 0.585, 0.005, 10), (20, 0.610, 0.005, 15), (999, 0.635, 0.005, 20)],
}
# EEA central government bonds in domestic currency carry no spread charge (Art. 180(2)).

# Correlation between market sub-modules (Art. 164). "A" = 0 when the interest
# rate UP shock is the binding one, 0.5 when the DOWN shock is binding.
MARKET_MODULES = ["interest", "equity", "property", "spread"]
def market_corr(down_binding: bool):
    a = 0.5 if down_binding else 0.0
    #                interest equity property spread
    return [
        [1.0,   a,    a,    a],     # interest
        [a,   1.0, 0.75, 0.75],     # equity
        [a,  0.75,  1.0,  0.5],     # property
        [a,  0.75,  0.5,  1.0],     # spread
    ]
# Currency (0.25 with all others) and concentration (0) are out of scope in v1.

# ---------------------------------------------------------------------------
# Life underwriting risk
# ---------------------------------------------------------------------------
MORTALITY_SHOCK = 0.15             # +15% to mortality rates, all ages (Art. 137)
LONGEVITY_SHOCK = -0.20            # -20% to mortality rates (Art. 138)
LAPSE_UP = 0.50                    # lapse rates x 1.5, capped at 100% (Art. 142)
LAPSE_DOWN = -0.50                 # lapse rates x 0.5, fall capped at 20 pp (Art. 142)
LAPSE_DOWN_MAX_ABS = 0.20
MASS_LAPSE = 0.40                  # immediate 40% discontinuance, retail business (Art. 142)
EXPENSE_LEVEL_SHOCK = 0.10         # +10% to expenses (Art. 140)
EXPENSE_INFLATION_SHOCK = 0.01     # +1 pp to expense inflation (Art. 140)
LIFE_CAT_SHOCK = 0.0015            # +0.15 pp to mortality in the next 12 months (Art. 143)
REVISION_SHOCK = 0.03              # +3% to revisable annuities (Art. 141) - not used in v1

LIFE_MODULES = ["mortality", "longevity", "lapse", "expense", "life_cat"]
# Correlations within life underwriting risk (Annex IV) - restricted to the v1 modules.
#                mort   long   lapse  exp   cat
LIFE_CORR = [
    [1.00, -0.25, 0.00, 0.25, 0.25],   # mortality
    [-0.25, 1.00, 0.25, 0.25, 0.00],   # longevity
    [0.00, 0.25, 1.00, 0.50, 0.25],    # lapse
    [0.25, 0.25, 0.50, 1.00, 0.25],    # expense
    [0.25, 0.00, 0.25, 0.25, 1.00],    # life cat
]

# ---------------------------------------------------------------------------
# Counterparty default risk (type 2 only in v1) (Art. 202)
# ---------------------------------------------------------------------------
TYPE2_FACTOR = 0.15
TYPE2_OVERDUE_INTERMEDIARY_FACTOR = 0.90   # receivables from intermediaries > 3 months overdue

# ---------------------------------------------------------------------------
# Basic SCR aggregation (Annex IV)
# ---------------------------------------------------------------------------
BSCR_MODULES = ["market", "default", "life", "health", "non_life"]
BSCR_CORR = [
    [1.00, 0.25, 0.25, 0.25, 0.25],    # market
    [0.25, 1.00, 0.25, 0.25, 0.50],    # default
    [0.25, 0.25, 1.00, 0.25, 0.00],    # life
    [0.25, 0.25, 0.25, 1.00, 0.00],    # health
    [0.25, 0.50, 0.00, 0.00, 1.00],    # non-life
]

# ---------------------------------------------------------------------------
# Operational risk (Art. 204)
# ---------------------------------------------------------------------------
OP_LIFE_PREMIUM_FACTOR = 0.04
OP_LIFE_TP_FACTOR = 0.0045
OP_CAP_BSCR = 0.30
OP_UNIT_LINKED_EXPENSE_FACTOR = 0.25

# ---------------------------------------------------------------------------
# MCR (Arts. 248-253) - life linear formula, simplified to two of its terms
# ---------------------------------------------------------------------------
MCR_FACTOR_OTHER_LIFE_TP = 0.021        # "other life (re)insurance obligations"
MCR_FACTOR_CAPITAL_AT_RISK = 0.0007     # total capital at risk
MCR_CORRIDOR = (0.25, 0.45)             # 25%-45% of SCR (Art. 248)
AMCR_LIFE = 4_000_000                   # absolute floor, EUR - VERIFY (indexed periodically)
