"""End-to-end analysis. Run from the repo root:  python -m analysis.run_all

Steps (mirrors brief/brief.md):
  1. Build the metric layer and run data tests
  2. Validity checks: sample ratio, covariate balance
  3. A/B analysis on the training split: IRR and net value per send, with CIs
  4. Targeting: choose a policy by 5-fold cross-validation on training only
  5. Evaluate send-all / send-none / chosen policy ONCE on the holdout, with bootstrap CIs
Writes analysis/outputs/results.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

from analysis import stats as st
from metrics.layer import MetricLayer

OUT = Path(__file__).resolve().parent / "outputs"
SEED = 7
CATEGORICAL = ["v1", "v4", "v5", "v6", "v7"]
CONTINUOUS = ["v2", "v3"]


# ---------------------------------------------------------------- helpers
def arm_counts(layer: MetricLayer, where: str) -> dict:
    r = layer.query(["promotion_customers", "promotion_purchases", "control_customers", "control_purchases"],
                    where=where).iloc[0]
    return {k: int(v) for k, v in r.items()}


def features(df: pd.DataFrame) -> pd.DataFrame:
    X = pd.get_dummies(df[CATEGORICAL].astype("category"), drop_first=False).astype(float)
    for c in CONTINUOUS:
        X[c] = df[c]
    return X


# ---------------------------------------------------------------- policy learners
# Each learner takes a training frame and returns a function: frame -> boolean target mask.

def learn_segment_rule(train: pd.DataFrame, break_even: float, min_cell: int = 1000):
    """Interpretable rule: target the V4 x V5 cells whose observed lift beats break-even."""
    g = train.groupby(["v4", "v5"])
    cells = []
    for key, d in g:
        if len(d) < min_cell:
            continue
        t, c = d[d.treated], d[~d.treated]
        if t.purchased.mean() - c.purchased.mean() > break_even:
            cells.append(key)
    cells = set(cells)
    return (lambda df: np.array([(a, b) in cells for a, b in zip(df.v4, df.v5)]), sorted(cells))


def learn_t_learner(train: pd.DataFrame, break_even: float, kind: str):
    """T-learner: separate purchase models per arm; target where predicted lift beats break-even."""
    def make():
        if kind == "logistic":
            return LogisticRegression(C=1.0, max_iter=2000)
        return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200,
                                              min_samples_leaf=200, random_state=SEED)
    X = features(train)
    m_t, m_c = make(), make()
    m_t.fit(X[train.treated.values], train.purchased[train.treated])
    m_c.fit(X[~train.treated.values], train.purchased[~train.treated])
    cols = X.columns

    def policy(df):
        Xd = features(df).reindex(columns=cols, fill_value=0.0)
        uplift = m_t.predict_proba(Xd)[:, 1] - m_c.predict_proba(Xd)[:, 1]
        return uplift > break_even
    return policy, None


LEARNERS = {
    "segment_rule_v4_v5": lambda tr, be: learn_segment_rule(tr, be),
    "t_learner_logistic": lambda tr, be: learn_t_learner(tr, be, "logistic"),
    "t_learner_gbm":      lambda tr, be: learn_t_learner(tr, be, "gbm"),
}


# ---------------------------------------------------------------- main
def main() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    layer = MetricLayer()
    tests = layer.build()
    rev, cost = layer.econ["revenue_per_purchase"], layer.econ["cost_per_promotion"]
    break_even = cost / rev
    results: dict = {"economics": {"revenue_per_purchase": rev, "cost_per_promotion": cost, "break_even_irr": break_even},
                     "data_tests": tests}

    df = pd.read_sql_query("select * from stg_customers", layer.conn)
    df["treated"] = df.arm.eq("promotion")
    train, hold = df[df.split == "training"].reset_index(drop=True), df[df.split == "holdout"].reset_index(drop=True)
    results["rows"] = {"training": len(train), "holdout": len(hold)}

    # ---- 2. validity
    validity = {}
    for name, d in [("training", train), ("holdout", hold)]:
        c = arm_counts(layer, f"split = '{name}'")
        srm = st.srm_test(c["promotion_customers"], c["control_customers"])
        smd = {v: st.standardized_mean_difference(d.loc[d.treated, v].values, d.loc[~d.treated, v].values)
               for v in CATEGORICAL + CONTINUOUS}
        validity[name] = {"srm": srm, "smd": smd, "max_abs_smd": max(abs(x) for x in smd.values())}
    results["validity"] = validity

    # ---- 3. A/B analysis (training split is the analysis sample; holdout is a replication)
    ab = {}
    for name in ["training", "holdout"]:
        c = arm_counts(layer, f"split = '{name}'")
        r = st.diff_in_proportions(c["promotion_purchases"], c["promotion_customers"],
                                   c["control_purchases"], c["control_customers"])
        r["counts"] = c
        r["net_value_per_send"] = rev * r["diff"] - cost
        r["net_value_per_send_ci"] = [rev * r["ci_low"] - cost, rev * r["ci_high"] - cost]
        r["nir_per_100k"] = 100_000 * r["net_value_per_send"]
        r["nir_per_100k_ci"] = [100_000 * x for x in r["net_value_per_send_ci"]]
        r["mde_80pct_power"] = st.mde(r["p_control"], c["promotion_customers"], c["control_customers"])
        # Cross-check: the metric layer must agree with the stats module
        lay = layer.query(["incremental_response_rate", "net_value_per_send"], where=f"split = '{name}'").iloc[0]
        assert abs(lay.incremental_response_rate - r["diff"]) < 1e-12
        assert abs(lay.net_value_per_send - r["net_value_per_send"]) < 1e-12
        ab[name] = r
    results["ab_test"] = ab
    tr = ab["training"]
    if tr["ci_low"] > break_even:
        blanket = "send_to_everyone"
    elif tr["ci_high"] < break_even:
        blanket = "do_not_send_to_everyone"
    else:
        blanket = "inconclusive"
    results["blanket_decision"] = blanket

    # ---- 4. choose a targeting policy by CV on training only
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    strata = train.treated.astype(int) * 2 + train.purchased
    cv = {k: [] for k in ["send_all", *LEARNERS]}
    cv_share = {k: [] for k in LEARNERS}
    rule_cells_by_fold = []
    for fit_idx, val_idx in skf.split(train, strata):
        fit, val = train.iloc[fit_idx], train.iloc[val_idx]
        tv, pv = val.treated.values, val.purchased.values
        cv["send_all"].append(st.policy_value(np.ones(len(val), bool), tv, pv, rev, cost))
        for k, learn in LEARNERS.items():
            pol, cells = learn(fit, break_even)
            if k == "segment_rule_v4_v5":
                rule_cells_by_fold.append([list(map(int, c)) for c in cells])
            tgt = pol(val)
            cv[k].append(st.policy_value(tgt, tv, pv, rev, cost))
            cv_share[k].append(float(tgt.mean()))
    cv_summary = {k: {"mean_value_per_customer": float(np.mean(v)), "fold_values": v,
                      "mean_share_targeted": float(np.mean(cv_share[k])) if k in cv_share else 1.0}
                  for k, v in cv.items()}
    chosen = max(LEARNERS, key=lambda k: cv_summary[k]["mean_value_per_customer"])
    results["targeting_cv"] = {"summary": cv_summary, "chosen_policy": chosen,
                               "rule_cells_by_fold": rule_cells_by_fold,
                               "rule_cells_stable": all(c == rule_cells_by_fold[0] for c in rule_cells_by_fold)}

    # Refit every learner on all of training. Only the chosen one is the pre-selected policy;
    # the others are reported on the holdout for transparency, clearly labelled as secondary.
    fitted = {k: learn(train, break_even) for k, learn in LEARNERS.items()}
    results["targeting_rule_cells"] = [list(map(int, c)) for c in fitted["segment_rule_v4_v5"][1]]

    # ---- 5. holdout evaluation, touched once
    th, ph = hold.treated.values, hold.purchased.values
    policies = {"send_all": np.ones(len(hold), bool), "send_none": np.zeros(len(hold), bool)}
    policies.update({k: fitted[k][0](hold) for k in LEARNERS})
    boot = st.bootstrap_policy_values(policies, th, ph, rev, cost, n_boot=2000, seed=SEED)
    hold_eval = {}
    for k, tgt in policies.items():
        point = st.policy_value(tgt, th, ph, rev, cost)
        lo, hi = np.nanpercentile(boot[k], [2.5, 97.5])
        diff_all = boot[k] - boot["send_all"]
        entry = {
            "share_targeted": float(tgt.mean()),
            "value_per_customer": point,
            "value_per_100k": 100_000 * point,
            "value_per_100k_ci": [100_000 * lo, 100_000 * hi],
            "vs_send_all_per_100k": 100_000 * (point - st.policy_value(policies["send_all"], th, ph, rev, cost)),
            "vs_send_all_per_100k_ci": [100_000 * x for x in np.nanpercentile(diff_all, [2.5, 97.5])],
            "prob_value_positive": float(np.nanmean(boot[k] > 0)),
        }
        if tgt.any():
            t, c = tgt & th, tgt & ~th
            irr_res = st.diff_in_proportions(int(ph[t].sum()), int(t.sum()), int(ph[c].sum()), int(c.sum()))
            entry["irr_in_targeted"] = irr_res["diff"]
            entry["irr_in_targeted_ci"] = [irr_res["ci_low"], irr_res["ci_high"]]
            # Original exercise scoring, for comparability: NIR on the targeted group as observed
            entry["exercise_nir"] = float(rev * ph[t].sum() - cost * t.sum() - rev * ph[c].sum())
        hold_eval[k] = entry
    results["holdout_evaluation"] = hold_eval

    ch = hold_eval[chosen]
    meets = ch["value_per_100k_ci"][0] > 0 and ch["vs_send_all_per_100k_ci"][0] > 0
    results["targeting_decision"] = "target" if meets else "inconclusive"

    # ---- 6. diagnostics that test the recommendation
    rule_tgt = policies["segment_rule_v4_v5"]
    rule = hold_eval["segment_rule_v4_v5"]

    # 6a. Overlap between the pre-selected model and the rule
    model_tgt = policies[chosen]
    results["policy_overlap"] = {
        "model_targets_inside_rule": float((model_tgt & rule_tgt).sum() / model_tgt.sum()),
        "rule_targets_covered_by_model": float((model_tgt & rule_tgt).sum() / rule_tgt.sum()),
    }

    # 6b. The customers the rule leaves out: does excluding them cost anything?
    excl = ~rule_tgt
    t, c = excl & th, excl & ~th
    ex = st.diff_in_proportions(int(ph[t].sum()), int(t.sum()), int(ph[c].sum()), int(c.sum()))
    results["excluded_by_rule"] = {
        "share": float(excl.mean()), "irr": ex["diff"], "irr_ci": [ex["ci_low"], ex["ci_high"]],
        "value_per_100k_if_sent": 100_000 * excl.mean() * (rev * ex["diff"] - cost),
    }

    # 6c. Sensitivity: value per extra sale (price vs margin) and promotion cost
    irr_rule, irr_all = rule["irr_in_targeted"], hold_eval["send_all"]["irr_in_targeted"]
    sens = []
    for value in [10.0, 9.0, 8.0, 7.0, 6.0, 5.0]:
        for c_ in [0.10, 0.15, 0.20, 0.25]:
            sens.append({"value_per_sale": value, "cost_per_send": c_,
                         "rule_per_100k": 100_000 * rule["share_targeted"] * (value * irr_rule - c_),
                         "send_all_per_100k": 100_000 * (value * irr_all - c_)})
    results["sensitivity"] = {
        "grid": sens,
        "rule_break_even_value_per_sale": cost / irr_rule,
        "rule_break_even_cost_per_send": rev * irr_rule,
        "rule_irr_ci_low_break_even_value_per_sale": cost / rule["irr_in_targeted_ci"][0],
    }

    # 6d. Rollout sizing: customers needed in the targeted segment (90% promoted / 10% held out)
    # to show the lift beats break-even (one-sided alpha 0.05, 80% power), if the holdout lift is the truth.
    t, c = rule_tgt & th, rule_tgt & ~th
    p_c, p_t = float(ph[c].mean()), float(ph[t].mean())
    from scipy.stats import norm
    se_needed = (irr_rule - break_even) / (norm.ppf(0.95) + norm.ppf(0.80))
    n_total = (p_t * (1 - p_t) / 0.9 + p_c * (1 - p_c) / 0.1) / se_needed ** 2
    results["rollout_sizing"] = {"assumed_irr": irr_rule, "control_rate": p_c, "treated_rate": p_t,
                                 "holdout_share": 0.10, "customers_needed": int(np.ceil(n_total))}

    # 6e. Segment lift with CIs on both splits, from metric-layer counts
    rows = []
    for split_name in ["training", "holdout"]:
        cnt = layer.query(["customers", "promotion_customers", "promotion_purchases",
                           "control_customers", "control_purchases"], ["v4", "v5"], f"split = '{split_name}'")
        for _, r_ in cnt.iterrows():
            d = st.diff_in_proportions(r_.promotion_purchases, r_.promotion_customers,
                                       r_.control_purchases, r_.control_customers)
            rows.append({"split": split_name, "v4": int(r_.v4), "v5": int(r_.v5), "customers": int(r_.customers),
                         "irr": d["diff"], "irr_ci_low": d["ci_low"], "irr_ci_high": d["ci_high"],
                         "net_value_per_send": rev * d["diff"] - cost})
    pd.DataFrame(rows).to_csv(OUT / "segment_lift.csv", index=False)
    (OUT / "results.json").write_text(json.dumps(results, indent=2, default=float))
    return results


if __name__ == "__main__":
    r = main()
    tr = r["ab_test"]["training"]
    print(f"Data tests: {sum(t['passed'] for t in r['data_tests'])}/{len(r['data_tests'])} passed")
    for s, v in r["validity"].items():
        print(f"[{s}] SRM ratio {v['srm']['observed_ratio']:.4f} p={v['srm']['p_value']:.3f}  max|SMD| {v['max_abs_smd']:.4f}")
    print(f"IRR {tr['diff']*100:.2f} pts (95% CI {tr['ci_low']*100:.2f} to {tr['ci_high']*100:.2f}), p={tr['p_value']:.2g}; "
          f"break-even {r['economics']['break_even_irr']*100:.1f} pts -> {r['blanket_decision']}")
    print(f"NIR per 100k sent: ${tr['nir_per_100k']:,.0f} (CI ${tr['nir_per_100k_ci'][0]:,.0f} to ${tr['nir_per_100k_ci'][1]:,.0f}); MDE {tr['mde_80pct_power']*100:.2f} pts")
    print("CV (training) value per 100k:")
    for k, v in r["targeting_cv"]["summary"].items():
        print(f"  {k:22s} ${100000*v['mean_value_per_customer']:>8,.0f}  share {v['mean_share_targeted']:.2f}")
    print(f"Chosen: {r['targeting_cv']['chosen_policy']}  rule cells: {r['targeting_rule_cells']}")
    print("Holdout:")
    for k, v in r["holdout_evaluation"].items():
        print(f"  {k:22s} share {v['share_targeted']:.2f}  value/100k ${v['value_per_100k']:>8,.0f} "
              f"CI [${v['value_per_100k_ci'][0]:,.0f}, ${v['value_per_100k_ci'][1]:,.0f}]  "
              f"vs all ${v['vs_send_all_per_100k']:,.0f} CI [${v['vs_send_all_per_100k_ci'][0]:,.0f}, ${v['vs_send_all_per_100k_ci'][1]:,.0f}]  "
              f"P(>0) {v['prob_value_positive']:.2f}")
    print(f"Targeting decision: {r['targeting_decision']}")
