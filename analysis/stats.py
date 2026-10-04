"""Statistical helpers. Definitions live in the metric layer; this module adds uncertainty."""

from __future__ import annotations

import numpy as np
from scipy import stats


def diff_in_proportions(x_t: int, n_t: int, x_c: int, n_c: int, alpha: float = 0.05) -> dict:
    """Difference in proportions (treatment - control) with a Wald CI and two-sided z-test."""
    p_t, p_c = x_t / n_t, x_c / n_c
    diff = p_t - p_c
    se = np.sqrt(p_t * (1 - p_t) / n_t + p_c * (1 - p_c) / n_c)
    z_crit = stats.norm.ppf(1 - alpha / 2)
    # Pooled SE for the hypothesis test of no difference
    p_pool = (x_t + x_c) / (n_t + n_c)
    se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / n_t + 1 / n_c))
    z = diff / se_pool
    return {
        "p_treatment": p_t,
        "p_control": p_c,
        "diff": diff,
        "se": se,
        "ci_low": diff - z_crit * se,
        "ci_high": diff + z_crit * se,
        "z": z,
        "p_value": float(2 * stats.norm.sf(abs(z))),
    }


def srm_test(n_t: int, n_c: int, expected_ratio: float = 0.5) -> dict:
    """Chi-square sample ratio mismatch test."""
    total = n_t + n_c
    expected = [total * expected_ratio, total * (1 - expected_ratio)]
    chi2, p = stats.chisquare([n_t, n_c], f_exp=expected)
    return {"n_treatment": n_t, "n_control": n_c, "observed_ratio": n_t / total, "chi2": chi2, "p_value": p}


def standardized_mean_difference(x_t: np.ndarray, x_c: np.ndarray) -> float:
    pooled_sd = np.sqrt((np.var(x_t, ddof=1) + np.var(x_c, ddof=1)) / 2)
    return float((np.mean(x_t) - np.mean(x_c)) / pooled_sd) if pooled_sd > 0 else 0.0


def mde(p_control: float, n_t: int, n_c: int, alpha: float = 0.05, power: float = 0.8) -> float:
    """Minimum detectable absolute lift for a two-sided test."""
    se = np.sqrt(p_control * (1 - p_control) * (1 / n_t + 1 / n_c))
    return float((stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)) * se)


def policy_value(target: np.ndarray, treated: np.ndarray, purchased: np.ndarray,
                 revenue: float, cost: float) -> float:
    """Expected incremental profit per customer in the population, relative to sending no one.

    Uses the randomized arms inside the targeted group to estimate the lift there:
        value = share_targeted * (revenue * IRR_targeted - cost)
    """
    if target.sum() == 0:
        return 0.0
    t, c = target & treated, target & ~treated
    if t.sum() == 0 or c.sum() == 0:
        return float("nan")
    irr = purchased[t].mean() - purchased[c].mean()
    return float(target.mean() * (revenue * irr - cost))


def bootstrap_policy_values(policies: dict[str, np.ndarray], treated: np.ndarray, purchased: np.ndarray,
                            revenue: float, cost: float, n_boot: int = 2000, seed: int = 7) -> dict[str, np.ndarray]:
    """Bootstrap the value of fixed policies (stratified by arm). Same resamples for every policy,
    so differences between policies are paired."""
    rng = np.random.default_rng(seed)
    idx_t, idx_c = np.flatnonzero(treated), np.flatnonzero(~treated)
    out = {k: np.empty(n_boot) for k in policies}
    for b in range(n_boot):
        idx = np.concatenate([rng.choice(idx_t, idx_t.size), rng.choice(idx_c, idx_c.size)])
        tr, pu = treated[idx], purchased[idx]
        for k, tgt in policies.items():
            out[k][b] = policy_value(tgt[idx], tr, pu, revenue, cost)
    return out
