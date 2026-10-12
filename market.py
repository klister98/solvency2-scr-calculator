"""Market risk: interest rate, equity, property and spread sub-modules."""
import numpy as np

import params as P
from aggregate import aggregate
from curve import shocked_curve


def _spread_factor(duration: float, cqs: int) -> float:
    for upper, a, b, lower in P.SPREAD_FACTORS[cqs]:
        if duration <= upper:
            return min(a + b * (duration - lower), 1.0)
    raise ValueError("duration out of range")


def interest_rate(ins) -> dict:
    """Loss in own funds under the up and down curve shocks; the larger one binds."""
    base_assets = ins.total_assets()
    base_bel = ins.bel()["total"]
    result = {}
    for direction in ("up", "down"):
        c = shocked_curve(ins.curve, direction)
        d_assets = ins.total_assets(c) - base_assets
        d_bel = ins.bel(curve=c)["total"] - base_bel
        result[direction] = max(0.0, -(d_assets - d_bel))   # loss in own funds
    binding = "down" if result["down"] > result["up"] else "up"
    return {"charge": result[binding], "up": result["up"], "down": result["down"], "binding": binding}


def equity(ins) -> dict:
    sa = float(np.clip(ins.symmetric_adjustment, *P.SA_BOUNDS))
    t1 = ins.other.equity_type1 * (P.EQUITY_SHOCK_TYPE1 + sa)
    t2 = ins.other.equity_type2 * (P.EQUITY_SHOCK_TYPE2 + sa)
    rho = P.EQUITY_TYPE1_TYPE2_CORR
    charge = float(np.sqrt(t1**2 + 2 * rho * t1 * t2 + t2**2))
    return {"charge": charge, "type1": t1, "type2": t2, "symmetric_adjustment": sa}


def property_risk(ins) -> dict:
    return {"charge": ins.other.property * P.PROPERTY_SHOCK}


def spread(ins) -> dict:
    table = ins.bond_table()
    corp = table[table["type"] == "corp"].copy()
    corp["factor"] = [_spread_factor(d, int(q)) for d, q in zip(corp["duration"], corp["cqs"])]
    corp["charge"] = corp["market_value"] * corp["factor"]
    return {"charge": float(corp["charge"].sum()), "detail": corp[["name", "cqs", "duration", "market_value", "factor", "charge"]]}


def market(ins) -> dict:
    ir = interest_rate(ins)
    eq = equity(ins)
    pr = property_risk(ins)
    sp = spread(ins)
    charges = [ir["charge"], eq["charge"], pr["charge"], sp["charge"]]
    corr = P.market_corr(down_binding=(ir["binding"] == "down"))
    total = aggregate(charges, corr)
    return {
        "charge": total,
        "sub": dict(zip(P.MARKET_MODULES, charges)),
        "undiversified": sum(charges),
        "interest_detail": ir,
        "equity_detail": eq,
        "spread_detail": sp["detail"],
    }
