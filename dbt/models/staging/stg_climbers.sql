select
    user_id,
    country,
    sex,
    height,
    weight,
    cast(age as int) as age,
    years_cl,
    cast(date_first as date) as date_first,
    cast(date_last as date) as date_last,
    grades_count,
    grades_first,
    grades_last,
    grades_max,
    round(grades_mean, 2) as grades_mean,
    year_first,
    year_last
from {{ source('raw', 'climbers') }}