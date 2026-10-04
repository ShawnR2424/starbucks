# Recommendation: Don't send the promotion to everyone. Send it only to the segment that responds.

**To:** Marketing lead · **Re:** $10 product promotion test · **Data:** 126,184 customers in a randomized test (84,534 analysis sample, 41,650 held out)

## The answer

1. **Stop the blanket send.** The promotion lifts purchase rate by **0.95 points** (95% CI 0.80 to 1.09). It needs **1.5 points** to cover its $0.15 cost on a $10 product. Sending to everyone loses about **$5,500 per 100,000 customers** (CI −$7,000 to −$4,100).
2. **Send only to customers with V4=2 and V5 in {1, 3}**, about 39% of the base. They respond at about **2.05 points**. On customers the analysis never saw, this earns about **+$2,100 per 100,000 customers** (95% CI +$600 to +$3,700), a swing of about **$7,500 per 100k** compared with sending to everyone. It also cuts promotion volume by about 60%.
3. **Before rolling out, confirm the $10 is the right value per sale.** If the profit from an extra sale is below about **$7.30**, even the targeted send loses money (see Risks).

![Lift vs break-even](figures/01_blanket_lift_vs_breakeven.png)

## Why

**The promotion works, but not well enough to pay for itself everywhere.** The lift is highly significant (p < 0.001), and a replication on the held-out customers gives the same answer (0.96 points, CI 0.75 to 1.16). The question was never whether the lift was real. It was whether the lift was worth $0.15 a send, and across the whole base it isn't.

**The response is concentrated.** Customers with V4=1 (about a third of the base) show no response at all. Among V4=2, the V5=1 and V5=3 groups respond at about 2 points, above break-even. The other V4=2 groups don't clear the bar.

![Lift by segment](figures/02_lift_by_segment.png)

**The targeting holds up on new customers.** I picked the targeting approach with cross-validation on the analysis sample only, then scored it once on the held-out customers. All three approaches tested were profitable on the holdout, and all beat sending to everyone by $7,000 to $7,500 per 100k. The pre-selected model and the simple V4/V5 rule target largely the same people: 94% of the model's picks fall inside the rule.

![Policy value on holdout](figures/03_policy_value_holdout.png)

## Risks and what would change this call

- **Value per sale.** The analysis treats each extra purchase as worth $10, the price. If the real contribution margin is lower, break-even rises. At a margin below about $7.30 per unit, the targeted segment's 2.05-point lift no longer covers the $0.15 cost, and the right call is to send to no one. **This is the single most important number to confirm.**
- **Promotion cost.** Targeting stays profitable up to a cost of about $0.20 per send. Above that, stop.
- **Small dollars, wide intervals.** Purchases are rare (about 1%), so the profit estimate for targeting ranges from about +$600 to +$3,700 per 100k. The direction is clear, but the size isn't precise.
- **We can say who responds, not why.** V1 to V7 are anonymized. Knowing what V4 and V5 represent would make the targeting easier to defend and to maintain.

## Recommended next step

Roll out to the targeted segment, but **keep a randomly held-out 10% of that segment unpromoted**. That keeps the lift measurable in production, catches drift, and builds a larger sample to tighten the profit estimate. Re-check after one cycle against the 1.5-point break-even (or the margin-adjusted break-even, once known).

---

## Appendix: method and diagnostics

**Pre-registration.** The question, metrics, and decision rules were committed in [`brief/brief.md`](../brief/brief.md) before any effect estimates. Two changes made afterwards are logged in its changelog.

**Validity checks (both passed).**

| Check | Analysis sample | Holdout |
|---|---|---|
| Sample ratio (promotion share) | 0.5011, χ² p = 0.51 | 0.4982, χ² p = 0.45 |
| Largest covariate imbalance, \|SMD\| across V1 to V7 | 0.015 | 0.013 |
| Data tests (unique IDs, no nulls, binary outcome) | 5/5 pass | |

An SMD under 0.1 is the usual bar for balance, and every feature is well under it.

**A/B result (analysis sample).** Promotion: 721 purchases out of 42,364 (1.70%). Control: 319 out of 42,170 (0.76%). The difference is 0.95 points, with a Wald 95% CI of 0.80 to 1.09, z = 12.5. The test could detect lifts as small as 0.17 points at 80% power. A confident "below 1.5 points" is therefore a finding, not a power problem. Net value per send is −$0.055.

**Targeting.** I compared three candidate policies by 5-fold cross-validated profit on the analysis sample:

| Policy | CV profit per 100k (fold SD) | Holdout profit per 100k (95% CI) | Share sent (holdout) |
|---|---|---|---|
| Rule: V4=2 and V5 in {1,3} | $2,029 (±$745) | $2,117 ($603 to $3,743) | 39% |
| Logistic T-learner, **pre-selected** | $2,084 (±$987) | $1,573 ($190 to $3,015) | 31% |
| Boosted-tree T-learner | $1,775 (±$709) | $2,108 ($695 to $3,611) | 36% |
| Send to everyone | −$5,545 | −$5,407 (−$7,432 to −$3,294) | 100% |

Cross-validation picked the logistic model by $55 per 100k, a gap less than a tenth of the fold-to-fold standard deviation, which is noise. The brief's decision rule ("target" if the pre-selected policy's profit CI excludes zero and it beats send-all) is met: +$1,573 (CI $190 to $3,015), and +$6,980 over send-all (CI $5,435 to $8,508).

The memo recommends the **rule** as the operational version. It is a judgment call, and I'm flagging it as one. The model and rule were indistinguishable in cross-validation, and they target mostly the same customers. The rule is explainable in one sentence and needs no model in production. The rule also scored higher on the holdout, but that was **not** the reason for the choice, and the recommendation would be the same if it had scored slightly lower.

Holdout profit uses the randomized arms inside each targeted group: profit = share targeted × ($10 × lift in targeted group − $0.15). The 95% CIs come from 2,000 bootstrap resamples, stratified by arm, with the same resamples used for every policy so that differences between policies are paired.

**Reproduce.** `make all` (or see the README).
