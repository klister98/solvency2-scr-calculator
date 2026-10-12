"""Operational risk (Art. 204), life business without unit-linked contracts.

Op = max(4% x earned life premiums, 0.45% x life technical provisions excl. risk margin),
capped at 30% of the basic SCR. The premium-growth term is ignored (no premium history).
"""
import params as P


def operational(ins, bscr: float) -> dict:
    earned_premiums = float(ins.term.loc[ins.term["term"] > 0, "annual_premium"].sum())
    tp_life = max(0.0, ins.bel()["total"])
    op_premiums = P.OP_LIFE_PREMIUM_FACTOR * earned_premiums
    op_provisions = P.OP_LIFE_TP_FACTOR * tp_life
    op = max(op_premiums, op_provisions)
    cap = P.OP_CAP_BSCR * bscr
    return {"charge": min(op, cap), "op_premiums": op_premiums, "op_provisions": op_provisions, "cap": cap}
