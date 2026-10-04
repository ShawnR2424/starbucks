"""Charts for the memo. Run after run_all:  python -m analysis.figures"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "outputs"
FIG = ROOT / "memo" / "figures"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
ACCENT = "#2a78d6"   # highlighted entity
MUTED = "#b4b2ab"    # de-emphasised entity (neutral, always paired with labels)
THRESH = "#52514e"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlelocation": "left",
})


def money(v: float) -> str:
    """Dollar label safe from matplotlib mathtext, with a true minus sign."""
    return ("−" if v < 0 else "") + f"\\${abs(v):,.0f}"


def _title(ax, title, subtitle):
    ax.set_title(title, pad=26, color=INK)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, color=INK_2, fontsize=9.5, va="bottom")


def fig_blanket(r: dict) -> None:
    be = r["economics"]["break_even_irr"] * 100
    rows = [("Training\n(analysis sample)", r["ab_test"]["training"]), ("Holdout\n(replication)", r["ab_test"]["holdout"])]
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    for i, (lab, a) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.plot([a["ci_low"] * 100, a["ci_high"] * 100], [y, y], color=ACCENT, lw=2, solid_capstyle="round")
        ax.plot(a["diff"] * 100, y, "o", ms=9, color=ACCENT, mec=SURFACE, mew=2)
        ax.text(a["diff"] * 100, y + 0.22, f"{a['diff']*100:.2f} pts  (95% CI {a['ci_low']*100:.2f}–{a['ci_high']*100:.2f})",
                ha="center", va="bottom", color=INK, fontsize=9.5)
    ax.axvline(be, color=THRESH, ls=(0, (4, 3)), lw=1.2)
    ax.text(be + 0.04, -0.45, "Break-even 1.5 pts\n(\\$0.15 cost ÷ \\$10 price)", color=INK_2, fontsize=9, va="bottom")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([lab for lab, _ in rows][::-1])
    ax.set_xlim(0, 2.6)
    ax.set_ylim(-0.6, len(rows) - 0.3)
    ax.set_xlabel("Incremental purchase rate from the promotion (percentage points)")
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    _title(ax, "Sending the promotion to everyone doesn't pay for itself",
           "The lift is real but stays below the 1.5-point break-even even at the top of its interval")
    fig.tight_layout()
    fig.savefig(FIG / "01_blanket_lift_vs_breakeven.png", dpi=200)
    plt.close(fig)


def fig_segments(r: dict) -> None:
    seg = pd.read_csv(OUT / "segment_lift_training.csv")
    cells = {tuple(c) for c in r["targeting_rule_cells"]}
    seg["targeted"] = [(a, b) in cells for a, b in zip(seg.v4, seg.v5)]
    seg["label"] = [f"V4={a}, V5={b}" for a, b in zip(seg.v4, seg.v5)]
    seg = seg.sort_values("incremental_response_rate", ascending=True).reset_index(drop=True)
    be = r["economics"]["break_even_irr"] * 100

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    colors = [ACCENT if t else MUTED for t in seg.targeted]
    ax.barh(seg.index, seg.incremental_response_rate * 100, height=0.62, color=colors, edgecolor=SURFACE, linewidth=2)
    for i, row in seg.iterrows():
        v = row.incremental_response_rate * 100
        x = max(v, 0) + 0.06
        ax.text(x, i, f"{v:.2f} pts · {row.customers/1000:.1f}k customers", va="center", fontsize=8.8,
                color=INK if row.targeted else INK_2, bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5))
    ax.axvline(be, color=THRESH, ls=(0, (4, 3)), lw=1.2)
    ax.text(be + 0.04, -0.75, "Break-even 1.5 pts", color=INK_2, fontsize=9, va="bottom")
    ax.axvline(0, color=INK_2, lw=0.8)
    ax.set_yticks(seg.index)
    ax.set_yticklabels(seg.label)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(-0.4, 3.9)
    ax.set_ylim(-0.9, len(seg) - 0.5)
    ax.set_xlabel("Incremental purchase rate from the promotion (percentage points, training data)")
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=ACCENT, label="Targeted"),
                       Patch(color=MUTED, label="Not targeted")],
              loc="lower right", bbox_to_anchor=(1.0, 0.08), frameon=False, fontsize=9)
    _title(ax, "Two segments clear break-even; most customers barely respond",
           "V4=2 with V5 in {1, 3} responds at ~2 pts; V4=1 shows no response")
    fig.tight_layout()
    fig.savefig(FIG / "02_lift_by_segment.png", dpi=200)
    plt.close(fig)


def fig_policies(r: dict) -> None:
    ev = r["holdout_evaluation"]
    chosen = r["targeting_cv"]["chosen_policy"]
    names = {
        "send_all": "Send to everyone",
        "send_none": "Send to no one",
        "segment_rule_v4_v5": "Rule: V4=2 and V5 in {1,3}",
        "t_learner_logistic": "Model: logistic T-learner",
        "t_learner_gbm": "Model: boosted-tree T-learner",
    }
    order = ["send_all", "send_none", "t_learner_gbm", "t_learner_logistic", "segment_rule_v4_v5"]
    fig, ax = plt.subplots(figsize=(9.6, 3.9))
    for y, k in enumerate(order):
        e = ev[k]
        targeting = k not in ("send_all", "send_none")
        col = ACCENT if targeting else MUTED
        lo, hi = e["value_per_100k_ci"]
        if hi > lo:
            ax.plot([lo, hi], [y, y], color=col, lw=2, solid_capstyle="round")
        ax.plot(e["value_per_100k"], y, "o", ms=9, color=col, mec=SURFACE, mew=2)
        txt = money(e["value_per_100k"])
        if hi > lo:
            txt += f"  ({money(lo)} to {money(hi)})"
        txt += f" · {e['share_targeted']*100:.0f}% sent"
        x = (hi if hi > lo else e["value_per_100k"]) + 250
        ax.text(x, y, txt, va="center", fontsize=8.8, color=INK if targeting else INK_2)
    ax.axvline(0, color=INK_2, lw=0.8)
    labels = [names[k] + ("  ★ pre-selected" if k == chosen else "") for k in order]
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(labels)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(-8500, 11500)
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(2000))
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: money(v / 1000) + "k"))
    ax.set_xlabel("Incremental profit per 100,000 customers vs sending no one (holdout, 95% bootstrap CI)")
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    _title(ax, "Targeting turns a loss into a profit on unseen customers",
           "All three targeting approaches are profitable on held-out customers")
    fig.tight_layout()
    fig.savefig(FIG / "03_policy_value_holdout.png", dpi=200)
    plt.close(fig)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    r = json.loads((OUT / "results.json").read_text())
    fig_blanket(r)
    fig_segments(r)
    fig_policies(r)
    print(f"Wrote figures to {FIG}")


if __name__ == "__main__":
    main()
