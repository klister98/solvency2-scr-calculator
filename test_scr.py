"""Sanity checks. Run from the project folder:  python -m pytest -q"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import curve as C  # noqa: E402
import liabilities as L  # noqa: E402
import params as P  # noqa: E402
import scr  # noqa: E402
from aggregate import aggregate  # noqa: E402
from insurer import Insurer  # noqa: E402
from modules.market import _spread_factor  # noqa: E402


@pytest.fixture(scope="module")
def ins():
    return Insurer.load()


@pytest.fixture(scope="module")
def result(ins):
    return scr.run(ins)


def test_aggregation_never_exceeds_simple_sum():
    charges = [10.0, 5.0, 3.0, 2.0]
    assert aggregate(charges, P.market_corr(True)) <= sum(charges) + 1e-9


def test_perfect_correlation_gives_simple_sum():
    assert aggregate([3.0, 4.0], [[1, 1], [1, 1]]) == pytest.approx(7.0)


def test_diversification_is_positive(result):
    assert result["diversification"] > 0
    assert result["bscr"] < result["sum_of_modules"]


def test_mortality_shock_raises_term_bel(ins):
    base = ins.bel()["term"]
    shocked = ins.bel(L.shocked(L.BEST_ESTIMATE, mortality_mult=1.15))["term"]
    assert shocked > base


def test_longevity_shock_raises_annuity_bel(ins):
    base = ins.bel()["annuity"]
    shocked = ins.bel(L.shocked(L.BEST_ESTIMATE, annuity_mortality_mult=0.80))["annuity"]
    assert shocked > base


def test_mcr_inside_corridor(result):
    m = result["mcr"]["mcr"]
    assert m >= P.AMCR_LIFE
    assert 0.25 * result["scr"] - 1e-6 <= m <= max(0.45 * result["scr"], P.AMCR_LIFE) + 1e-6


def test_operational_risk_capped(result):
    assert result["operational"]["charge"] <= 0.30 * result["bscr"] + 1e-6


def test_symmetric_adjustment_is_bounded():
    ins = Insurer.load(symmetric_adjustment=0.50)          # outside the +/-10% band
    from modules.market import equity
    assert equity(ins)["symmetric_adjustment"] == pytest.approx(0.10)


def test_up_shock_adds_at_least_one_point():
    base = C.base_curve()
    up = C.shocked_curve(base, "up")
    assert np.all(up[1:] - base[1:] >= 0.01 - 1e-12)


def test_spread_factor_known_points():
    assert _spread_factor(4.0, 0) == pytest.approx(0.036)          # 0.9% x 4
    assert _spread_factor(7.0, 1) == pytest.approx(0.055 + 0.012)  # 5.5% + 0.6% x 2


def test_balance_sheet_adds_up(result):
    bs = result["balance_sheet"]
    assert bs["own_funds"] == pytest.approx(bs["assets"] - bs["bel"] - bs["risk_margin"])
