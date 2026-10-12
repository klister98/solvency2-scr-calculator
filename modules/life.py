"""Life underwriting risk: each shock changes an assumption, re-projects and measures the BEL increase."""
import params as P
from aggregate import aggregate
from liabilities import BEST_ESTIMATE, shocked


def _increase(ins, basis) -> float:
    """Increase in BEL (= loss in own funds; assets do not move under life shocks)."""
    return max(0.0, ins.bel(basis)["total"] - ins._base_bel)


def life(ins) -> dict:
    ins._base_bel = ins.bel()["total"]
    be = BEST_ESTIMATE

    mortality = _increase(ins, shocked(be, mortality_mult=1 + P.MORTALITY_SHOCK))
    longevity = _increase(ins, shocked(be, annuity_mortality_mult=1 + P.LONGEVITY_SHOCK))

    up_rate = min(be.lapse_rate * (1 + P.LAPSE_UP), 1.0)
    down_rate = max(be.lapse_rate * (1 + P.LAPSE_DOWN), be.lapse_rate - P.LAPSE_DOWN_MAX_ABS)
    lapse_up = _increase(ins, shocked(be, lapse_rate=up_rate))
    lapse_down = _increase(ins, shocked(be, lapse_rate=down_rate))
    lapse_mass = _increase(ins, shocked(be, mass_lapse=P.MASS_LAPSE))
    lapse = max(lapse_up, lapse_down, lapse_mass)

    expense = _increase(ins, shocked(
        be, expense_mult=1 + P.EXPENSE_LEVEL_SHOCK,
        expense_inflation=be.expense_inflation + P.EXPENSE_INFLATION_SHOCK))
    cat = _increase(ins, shocked(be, cat_addition=P.LIFE_CAT_SHOCK))

    charges = [mortality, longevity, lapse, expense, cat]
    return {
        "charge": aggregate(charges, P.LIFE_CORR),
        "sub": dict(zip(P.LIFE_MODULES, charges)),
        "undiversified": sum(charges),
        "lapse_detail": {"up": lapse_up, "down": lapse_down, "mass": lapse_mass},
    }
