# Data

The raw dataset is not stored in this repository.

The data originated from a Starbucks take-home assessment and has no stated license, so it is downloaded from its public source instead of redistributed.

## Download

From the project root:

```bash
make data
```

The download script clones [01KAT1/Marketing-Promotion-Campaign-Uplift-Modelling-Starbucks-Dataset](https://github.com/01KAT1/Marketing-Promotion-Campaign-Uplift-Modelling-Starbucks-Dataset) and copies `training.csv` and `Test.csv` into this folder.

Other copies of the dataset:

- [Shuniy/starbucks](https://github.com/Shuniy/starbucks/tree/main)
- [Interview Query](https://www.interviewquery.com/takehomes/starbucks-promotion-strategy)

## Files

| File | Rows | Grain | Role |
|---|---|---|---|
| `training.csv` | 84,534 | One row per customer | Analysis sample: A/B inference, exploration, model fitting, cross-validation |
| `Test.csv` | 41,650 | One row per customer | Holdout: final policy evaluation only |

## Columns

| Column | Description |
|---|---|
| `ID` | Customer identifier |
| `Promotion` | `Yes` if the customer was randomly assigned to receive the promotion, `No` otherwise |
| `purchase` | `1` if the customer purchased the product, `0` otherwise |
| `V1` to `V7` | Anonymized customer features |

## Known Data Issues

`Test.csv` contains six extra unnamed columns with leftover spreadsheet notes in 6 rows.

The metric layer loads only the ten documented columns, so these notes never reach the analysis.
