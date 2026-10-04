# Experiment Brief: Starbucks Promotion

_Written before looking at any results. Edits after analysis begins must be logged in the changelog at the bottom._

## 1. Decision

**Stakeholder:** marketing lead deciding how to deploy a promotion.
**Decision:** send the promotion to (a) everyone, (b) no one, or (c) only customers predicted to respond.
**Cost of being wrong:** sending to everyone when the lift is below break-even loses money on every send. Sending to no one when a segment responds forgoes profit.

## 2. Economics and break-even

- Revenue per purchase: $10
- Cost per promotion sent: $0.15
- Break-even incremental purchase probability = 0.15 / 10 = **1.5 percentage points**

A promotion that lifts purchase probability by less than 1.5 points loses money on average, even if the lift is statistically significant.

## 3. Hypotheses

- H0: the promotion does not change purchase probability.
- H1: the promotion changes purchase probability.
- Business hypothesis: the lift exceeds 1.5 points for at least some identifiable segment, even if it does not for the population as a whole.

## 4. Metrics

| Role | Metric | Definition |
|---|---|---|
| Primary | Incremental response rate (IRR) | purchase rate (promotion) minus purchase rate (control) |
| Primary | Net incremental revenue (NIR) | 10 x purchases (promotion) - 0.15 x customers (promotion) - 10 x purchases (control), scaled to equal group sizes |
| Secondary | Purchase rate by group | purchases / customers |
| Guardrail | Randomization balance | V1 to V7 distributions similar across groups |
| Guardrail | Sample ratio | group sizes consistent with intended split |

## 5. Validity checks (run before any effect estimate)

1. Sample ratio between promotion and control groups.
2. Balance of V1 to V7 across groups.
3. Duplicate and missing-value checks.

If a check fails materially, stop and investigate before interpreting effects.

## 6. Decision rules

- **Send to everyone** only if the lower bound of the 95% interval on IRR exceeds 1.5 points and NIR is positive.
- **Send to no one** if the upper bound of the 95% interval on IRR is below 1.5 points and no segment qualifies under the targeting rule.
- **Target** if a targeting policy has positive NIR on the holdout set with its 95% interval excluding zero, and beats both send-all and send-none.
- Otherwise: **inconclusive**. Recommend a larger or longer test, and state the sample needed.

## 7. Targeting policy evaluation

- Create a holdout split from the labeled data before any modeling. The holdout is touched once, for final evaluation.
- Fit lift models on the training portion only.
- Compare send-all, send-none, and model-targeted policies by NIR on the holdout.
- Report uncertainty with bootstrap intervals.

## 8. Known limitations

- V1 to V7 are anonymized, so segments can be described but not explained.
- Purchases are rare, so intervals will be wide.
- The data comes from a screening assessment, so real-world generalization is unknown.

## Changelog

_No changes yet._
