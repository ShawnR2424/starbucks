# Starbucks Promotion: A/B Test + Metric Layer

**Question:** Should we send a promotion for a $10 product to everyone, to no one, or only to customers likely to respond? Each send costs $0.15.

## Answer

| | |
|---|---|
| **Recommendation** | Don't send to everyone. Send only to customers with **V4=2 and V5 in {1, 3}** (about 39% of the base). |
| **Why** | The promotion lifts purchases by **0.95 points** (95% CI 0.80 to 1.09), short of the **1.5-point break-even** ($0.15 ÷ $10). The targeted segment responds at **~2.05 points**. |
| **Impact** | Sending to everyone: **−$5,400 per 100k customers**. Targeted: **+$2,100 per 100k** (95% CI +$600 to +$3,700) on held-out customers, a ~$7,500 swing with ~60% fewer promotions sent. |
| **Main risk** | The $10 is price, not margin. If an extra sale is worth less than **~$7.30**, even the targeted send loses money. Confirm margin before rollout. |
| **Next step** | Roll out to the target segment with a 10% unpromoted holdout to keep measuring lift. |

**Read the one-page memo: [`memo/memo.md`](memo/memo.md)**

![Policy value on holdout](memo/figures/03_policy_value_holdout.png)

## How this was done

1. **Pre-registered brief** ([`brief/brief.md`](brief/brief.md)): decision, break-even logic, metrics, and decision rules written before any analysis, with a changelog for anything changed later.
2. **Metric layer** ([`metrics/`](metrics/)): every metric is defined once in [`metrics.yml`](metrics/metrics.yml), with a note on why it exists. [`layer.py`](metrics/layer.py) compiles metric requests into SQL against a staging model and runs dbt-style data tests first. The analysis asks the layer for metrics by name and never re-derives them.
3. **Validity checks**: sample ratio (χ² test) and covariate balance (standardized mean differences), on both splits.
4. **A/B inference**: difference in purchase rates with a 95% CI, converted to dollars, with the minimum detectable effect reported.
5. **Targeting**: three candidate policies (a V4×V5 segment rule, logistic and boosted-tree T-learners) compared by 5-fold cross-validation on training only. The selected policy and the alternatives are scored once on the untouched holdout, with paired bootstrap CIs.
6. **Memo** ([`memo/memo.md`](memo/memo.md)): one page for a product manager, with diagnostics in an appendix.

### Metric layer example

```bash
python -m metrics.layer query incremental_response_rate net_value_per_send --dims v4,v5 --where "split='training'"
python -m metrics.layer sql net_value_per_send --dims split    # show the compiled SQL
```

The SQL is portable (SQLite here, also DuckDB and Snowflake), and the YAML follows a dbt semantic model's structure (measures, dimensions, ratio and derived metrics), so it can move to dbt without changing any definitions.

## Reproduce

```bash
pip install -r requirements.txt
make data        # downloads training.csv and Test.csv into data/ (not committed; no stated license)
make all         # builds the metric layer, runs the analysis, renders figures
```

Outputs: `analysis/outputs/results.json` (every number in the memo) and `memo/figures/`.

## Repo layout

```
brief/      pre-registered question, decision rules, changelog
metrics/    metric definitions (YAML), staging SQL, compiler + data tests
analysis/   validity checks, A/B inference, targeting, figures
memo/       one-page recommendation + appendix
data/       download script (raw data not committed)
```

## Data source

Starbucks take-home assessment data, via [01KAT1/Marketing-Promotion-Campaign-Uplift-Modelling-Starbucks-Dataset](https://github.com/01KAT1/Marketing-Promotion-Campaign-Uplift-Modelling-Starbucks-Dataset). Features V1 to V7 are anonymized.
