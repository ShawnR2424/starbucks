# Data

Not committed: the dataset came from a Starbucks take-home assessment and no license is stated.

Get it with:

```bash
bash data/download.sh
```

This clones [01KAT1/Marketing-Promotion-Campaign-Uplift-Modelling-Starbucks-Dataset](https://github.com/01KAT1/Marketing-Promotion-Campaign-Uplift-Modelling-Starbucks-Dataset) and copies `training.csv` and `Test.csv` here. Other copies: [Shuniy/starbucks](https://github.com/Shuniy/starbucks/tree/main), [Interview Query](https://www.interviewquery.com/takehomes/starbucks-promotion-strategy).

| File | Rows | Role |
|---|---|---|
| `training.csv` | 84,534 | Analysis sample: A/B inference, exploration, model fitting, cross-validation |
| `Test.csv` | 41,650 | Holdout: final policy evaluation only |

Both files have `ID, Promotion (Yes/No), purchase (0/1), V1..V7`. `Test.csv` also has six stray columns of spreadsheet notes in 6 rows, which the staging model drops.
