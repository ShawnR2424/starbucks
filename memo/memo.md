# Recommendation: Stop the blanket promotion and send it only to the segment that responds

**To:** Marketing lead
**Re:** Promotion test for a $10 product
**Data:** 126,184 customers from a randomized test (84,534 in the analysis sample, 41,650 held out for final evaluation)

## Summary

1. **Stop sending the promotion to everyone.** It lifts purchase rate by **0.95 points** (95% CI 0.80 to 1.09), but it needs **1.5 points** to cover its $0.15 cost on a $10 product. Sending to everyone loses about **$5,400 per 100,000 customers** compared with sending nothing.
2. **Send it only to customers with V4=2 and V5 in {1, 3}**, about 39% of the base. They respond at **2.05 points** (CI 1.64 to 2.45), which clears break-even. On held-out customers this earns about **+$2,100 per 100,000 customers** (CI +$600 to +$3,700) and sends about 60% fewer promotions.
3. **Confirm what a sale is worth before rolling out.** The analysis treats each extra sale as worth the $10 price. If the real margin per sale is below **$7.33**, even the targeted send loses money.

Most of the gain comes from step 1. Of the roughly $7,500 per 100k difference between sending to everyone and targeting, about $5,400 comes from stopping a promotion that loses money. Targeting adds the remaining $2,100.

![Lift vs break-even](figures/01_blanket_lift_vs_breakeven.png)

## Why

**The promotion works, but not well enough to pay for itself across the whole base.** The lift is highly significant (p < 0.001), and the held-out customers show the same result (0.96 points, CI 0.75 to 1.16). The question was whether the lift was worth $0.15 per send. Across the whole base, it isn't.

**The response is concentrated in two segments.** Customers with V4=1 (about a third of the base) show no response. Among V4=2 customers, the V5=1 and V5=3 groups respond at about 2 points in both the training data and the holdout. The rest of the base responds a little (0.28 points, CI 0.06 to 0.50), but not nearly enough. Sending to them would lose about $7,500 per 100k customers.

![Lift by segment](figures/02_lift_by_segment.png)

**The targeting held up on customers it wasn't built on.** I selected the targeting approach using only the analysis sample and scored it once on the holdout. All three approaches I tested were profitable on the holdout and beat sending to everyone by $7,000 to $7,500 per 100k. They target largely the same people: 94% of the customers the selected model picks also fall inside the V4/V5 rule.

![Policy value on holdout](figures/03_policy_value_holdout.png)

## What would change this recommendation

**The value of a sale.** This matters most. The recommendation holds if an extra sale is worth at least $7.33. To be confident the targeted send pays off (using the low end of its lift interval), a sale needs to be worth about $9.10.

| Value per extra sale | Targeted send, per 100k | Send to everyone, per 100k |
|---|---|---|
| $10 (price) | +$2,117 | −$5,407 |
| $9 | +$1,326 | −$6,366 |
| $8 | +$534 | −$7,325 |
| $7 | −$258 | −$8,285 |
| $6 | −$1,049 | −$9,244 |

_Holdout estimates at a $0.15 cost per send._

**The cost per send.** Targeting stays profitable up to about $0.20 per send (+$184 per 100k at $0.20). At $0.25 it loses money.

**Effects this data can't measure.** The test records one purchase outcome per customer. It does not capture:
- promotion fatigue or unsubscribes
- whether customers who would have paid full price used the promotion instead
- longer-term changes in purchase behavior

The rollout should track these.

**Precision.** Purchases are rare (about 1%), so the profit estimate for targeting is wide (+$600 to +$3,700 per 100k). The direction is clear, but the exact size isn't.

**Time.** The holdout comes from the same test period, so it shows the result holds for new customers, not that it will hold in a future period.

**Explainability.** V1 to V7 are anonymized. Knowing what V4 and V5 represent would make the targeting easier to defend and to keep up to date.

## Recommended next steps

1. **Confirm the margin per sale** against the $7.33 threshold.
2. **Roll out to the targeted segment, keeping 10% of it unpromoted** as an ongoing control group. About **20,700 targeted customers** are enough to confirm the lift beats break-even (one-sided 95% confidence, 80% power, assuming the lift seen on the holdout is the true lift). Continue if the measured lift's lower bound stays above break-even. Stop if its upper bound falls below it.
3. **Test V4=2, V5=4 separately.** It is a small segment (about 4% of the base) whose lift sits right at break-even (1.32 points in training, 1.39 on the holdout, with intervals on both sides of 1.5). It was left out of the rule, but it isn't clearly unprofitable.

---

## Appendix: Method and Diagnostics

### Pre-registration

The question, metrics, and decision rules were committed in [`brief/brief.md`](../brief/brief.md) before the data was downloaded. The commit history shows the brief landing before any analysis. Two later changes are logged in its changelog.

### Validity checks

Both checks passed on both samples.

| Check | Analysis sample | Holdout |
|---|---|---|
| Sample ratio (share promoted) | 0.5011, χ² p = 0.51 | 0.4982, χ² p = 0.45 |
| Largest covariate imbalance, \|SMD\| across V1 to V7 | 0.015 | 0.013 |

All 8 data tests passed: unique IDs, no nulls, binary outcome, accepted arm values, features in range, and no customer in both samples. An SMD under 0.1 is the usual bar for balance.

All estimates are intent-to-treat: they compare customers assigned to receive the promotion with customers assigned not to, whether or not each customer actually saw it.

### A/B result (analysis sample)

| | Customers | Purchases | Purchase rate |
|---|---|---|---|
| Promotion | 42,364 | 721 | 1.70% |
| Control | 42,170 | 319 | 0.76% |

The lift is 0.95 points, with a Wald 95% CI of 0.80 to 1.09 (z = 12.5). The test could detect lifts as small as 0.17 points at 80% power, so finding the lift below 1.5 points is a real result, not a power problem.

### Targeting

Policies were compared by 5-fold cross-validated profit on the analysis sample.

| Policy | CV profit per 100k (fold SD) | Holdout profit per 100k (95% CI) | Share sent |
|---|---|---|---|
| Rule: V4=2 and V5 in {1, 3} | $2,029 (±$745) | $2,117 ($603 to $3,743) | 39% |
| Logistic T-learner (**pre-selected**) | $2,084 (±$987) | $1,573 ($190 to $3,015) | 31% |
| Boosted-tree T-learner | $1,775 (±$709) | $2,108 ($695 to $3,611) | 36% |
| Send to everyone | −$5,545 | −$5,407 (−$7,432 to −$3,294) | 100% |

Cross-validation picked the logistic model by $55 per 100k, less than a tenth of the fold-to-fold standard deviation. The brief's decision rule is met by that pre-selected policy: holdout profit of +$1,573 (CI $190 to $3,015), and +$6,980 over sending to everyone (CI $5,435 to $8,508).

I recommend the **rule** as the version to deploy, and I'm flagging that as a judgment call made after seeing results. The rule and the model were indistinguishable in cross-validation and target mostly the same customers. The rule fits in one sentence and needs no model in production. It also picked the same two segments in 4 of the 5 folds; the fifth fold added the borderline V4=2, V5=4 segment. The rule scored higher on the holdout than the model, but that wasn't the reason for choosing it, and the recommendation would be the same if it had scored slightly lower.

Holdout profit uses the randomized arms inside each targeted group: profit = share targeted × ($10 × lift in the targeted group − $0.15). The 95% CIs come from 2,000 bootstrap resamples stratified by arm. Every policy uses the same resamples, so differences between policies are paired.

For comparison with the original Starbucks exercise, which scores policies by IRR and NIR on the test set: the rule scores IRR 0.0205 and NIR $424.65 on the holdout.

### Reproduce

Run `make data && make all`. See the README for setup.
