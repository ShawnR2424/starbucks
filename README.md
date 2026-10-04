# Starbucks Promotion: A/B Test + Metric Layer

**Question:** Should we send the promotion to everyone, to no one, or only to customers likely to respond?

**Break-even rule:** the product earns $10 and each promotion costs $0.15, so the promotion only pays for itself if it raises purchase probability by more than 0.15 / 10 = **1.5 percentage points**.

_Status: scaffolding. Results and recommendation will be added here, answer first._

## Plan

1. `brief/`: pre-registered question, decision rule, primary and guardrail metrics
2. `metrics/`: metric layer, with each metric defined once and a note on why it exists
3. `analysis/`: reproducible validity checks, A/B analysis, targeting policy comparison
4. `memo/`: one-page recommendation for a product manager, diagnostics in an appendix

## Data

The dataset originates from a Starbucks take-home assessment and has no stated license, so the raw CSV is **not** committed. See `data/README.md` for how to obtain it.
