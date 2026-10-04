-- Staging model: one row per customer in the experiment.
-- Unions the two source files, tags which split each row belongs to,
-- standardises types, and drops stray spreadsheet columns present in Test.csv.
-- Portable SQL: runs on SQLite (default here), DuckDB, and Snowflake.

with unioned as (
    select ID, Promotion, purchase, V1, V2, V3, V4, V5, V6, V7, 'training' as split
    from raw_training
    union all
    select ID, Promotion, purchase, V1, V2, V3, V4, V5, V6, V7, 'holdout' as split
    from raw_test
)

select
    cast(ID as integer)                                   as customer_id,
    split,
    case when Promotion = 'Yes' then 'promotion'
         when Promotion = 'No'  then 'control' end        as arm,
    cast(purchase as integer)                             as purchased,
    cast(V1 as integer)                                   as v1,
    cast(V2 as real)                                      as v2,
    cast(V3 as real)                                      as v3,
    cast(V4 as integer)                                   as v4,
    cast(V5 as integer)                                   as v5,
    cast(V6 as integer)                                   as v6,
    cast(V7 as integer)                                   as v7,
    -- Quartile bins for the two continuous features, computed per split
    -- so holdout bins never use training information.
    ntile(4) over (partition by split order by V2)        as v2_quartile,
    ntile(4) over (partition by split order by V3)        as v3_quartile
from unioned
