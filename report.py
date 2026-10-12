"""
Run the calculator, print the results and save tables and charts to output/.

    python report.py
"""
import os
from dataclasses import replace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import curve as C
import scr
from insurer import Insurer

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT, exist_ok=True)
M = 1e6

INK, MUTED, GRID = "#1f2933", "#6b7785", "#e4e7eb"
CHARGE, REDUCTION, TOTAL = "#3d6fb6", "#9aa5b1", "#1f3a5f"


def results_table(r: dict) -> pd.DataFrame:
    rows = []
    for name, v in r["market"]["sub"].items():
        rows.append(("Market", name, v))
    rows.append(("Market", "diversification", r["market"]["charge"] - r["market"]["undiversified"]))
    rows.append(("Market", "TOTAL market", r["market"]["charge"]))
    for name, v in r["life"]["sub"].items():
        rows.append(("Life", name, v))
    rows.append(("Life", "diversification", r["life"]["charge"] - r["life"]["undiversified"]))
    rows.append(("Life", "TOTAL life", r["life"]["charge"]))
    rows.append(("Default", "type 2 receivables", r["default"]["charge"]))
    rows.append(("BSCR", "sum of modules", r["sum_of_modules"]))
    rows.append(("BSCR", "diversification between modules", -r["diversification"]))
    rows.append(("BSCR", "BSCR", r["bscr"]))
    rows.append(("SCR", "operational risk", r["operational"]["charge"]))
    rows.append(("SCR", "SCR", r["scr"]))
    rows.append(("MCR", "MCR", r["mcr"]["mcr"]))
    df = pd.DataFrame(rows, columns=["module", "item", "EUR"])
    df["EUR m"] = (df["EUR"] / M).round(2)
    return df


def waterfall(r: dict, path: str):
    steps = [
        ("Market", r["modules"]["market"], "charge"),
        ("Life", r["modules"]["life"], "charge"),
        ("Default", r["modules"]["default"], "charge"),
        ("Diversification", -r["diversification"], "reduction"),
        ("BSCR", r["bscr"], "total"),
        ("Operational", r["operational"]["charge"], "charge"),
        ("SCR", r["scr"], "total"),
    ]
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    running = 0.0
    for i, (label, v, kind) in enumerate(steps):
        if kind == "total":
            bottom, height, color = 0, v, TOTAL
            running = v
        else:
            bottom = running + min(v, 0)
            height = abs(v)
            color = CHARGE if kind == "charge" else REDUCTION
            running += v
        ax.bar(i, height / M, bottom=bottom / M, width=0.6, color=color)
        top = (bottom + height) / M
        ax.text(i, top + 0.6, f"{v / M:+.1f}" if kind != "total" else f"{v / M:.1f}",
                ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_xticks(range(len(steps)), [s[0] for s in steps], color=INK, fontsize=9)
    ax.set_ylabel("EUR million", color=MUTED, fontsize=9)
    ax.set_title(f"From module charges to the SCR   (solvency ratio {r['solvency_ratio']:.0%})",
                 loc="left", color=INK, fontsize=11)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", colors=MUTED, labelsize=8, length=0)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def sensitivities() -> pd.DataFrame:
    """What-if scenarios, each a fresh run of the full calculation."""
    base = Insurer.load()
    scenarios = {"Base": base}

    for sa in (-0.10, 0.10):
        scenarios[f"Symmetric adjustment {sa:+.0%}"] = Insurer.load(symmetric_adjustment=sa)

    shifted = Insurer.load()
    o = shifted.other
    move = 0.2 * o.equity_type1
    shifted.other = replace(o, equity_type1=o.equity_type1 - move, equity_type2=o.equity_type2 + move)
    scenarios["20% of type 1 equity moved to type 2"] = shifted

    scenarios["Risk-free rates -100bp"] = Insurer.load(curve=C.base_curve(level_shift=-0.01))

    doubled = Insurer.load()
    doubled.term = pd.concat([doubled.term, doubled.term], ignore_index=True)
    scenarios["Term assurance book doubled"] = doubled

    rows = []
    for name, ins in scenarios.items():
        r = scr.run(ins)
        rows.append({
            "scenario": name,
            "own funds (EUR m)": round(r["balance_sheet"]["own_funds"] / M, 1),
            "SCR (EUR m)": round(r["scr"] / M, 1),
            "solvency ratio": f"{r['solvency_ratio']:.0%}",
        })
    return pd.DataFrame(rows)


def main():
    ins = Insurer.load()
    r = scr.run(ins)
    bs = pd.Series(r["balance_sheet"]) / M
    table = results_table(r)

    print("\nSOLVENCY II BALANCE SHEET (EUR m)")
    print(bs.round(2).to_string())
    print("\nSCR BUILD-UP")
    print(table[["module", "item", "EUR m"]].to_string(index=False))
    print(f"\nInterest rate: binding shock = {r['market']['interest_detail']['binding']}")
    print(f"Solvency ratio = {r['solvency_ratio']:.1%}   MCR ratio = {r['mcr_ratio']:.1%}")

    sens = sensitivities()
    print("\nSENSITIVITIES")
    print(sens.to_string(index=False))

    table.to_csv(os.path.join(OUT, "scr_buildup.csv"), index=False)
    sens.to_csv(os.path.join(OUT, "sensitivities.csv"), index=False)
    waterfall(r, os.path.join(OUT, "scr_waterfall.png"))
    print(f"\nSaved results and chart to {OUT}")


if __name__ == "__main__":
    main()
