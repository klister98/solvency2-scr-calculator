"""Full standard formula run: modules -> BSCR -> operational risk -> SCR -> MCR -> solvency ratio."""
import params as P
from aggregate import aggregate
from modules.default import default
from modules.life import life
from modules.market import market
from modules.operational import operational


def mcr(ins, scr_value: float) -> dict:
    """Simplified life linear MCR, kept inside the 25%-45% corridor and above the absolute floor."""
    b = ins.bel()
    tp_other_life = max(0.0, b["total"])
    capital_at_risk = max(0.0, float(ins.term["sum_assured"].sum()) - max(0.0, b["term"]))
    linear = P.MCR_FACTOR_OTHER_LIFE_TP * tp_other_life + P.MCR_FACTOR_CAPITAL_AT_RISK * capital_at_risk
    lo, hi = P.MCR_CORRIDOR
    combined = min(max(linear, lo * scr_value), hi * scr_value)
    return {"mcr": max(combined, P.AMCR_LIFE), "linear": linear, "floor": lo * scr_value, "cap": hi * scr_value}


def run(ins) -> dict:
    bs = ins.balance_sheet()
    mk = market(ins)
    lf = life(ins)
    df = default(ins)

    module_charges = {"market": mk["charge"], "default": df["charge"], "life": lf["charge"], "health": 0.0, "non_life": 0.0}
    bscr = aggregate([module_charges[m] for m in P.BSCR_MODULES], P.BSCR_CORR)
    op = operational(ins, bscr)
    scr_value = bscr + op["charge"]          # no loss-absorbing capacity adjustments in v1
    m = mcr(ins, scr_value)

    return {
        "balance_sheet": bs,
        "market": mk, "life": lf, "default": df, "operational": op,
        "modules": module_charges,
        "sum_of_modules": sum(module_charges.values()),
        "bscr": bscr,
        "diversification": sum(module_charges.values()) - bscr,
        "scr": scr_value,
        "mcr": m,
        "solvency_ratio": bs["own_funds"] / scr_value,
        "mcr_ratio": bs["own_funds"] / m["mcr"],
    }
