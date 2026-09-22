select
    user_id,
    country,
    sex,
    height,
    weight,
    age,
    years_cl,
    date_first,
    date_last,
    grades_count,
    grades_first,
    grades_last,
    grades_max,
    grades_mean,
    year_first,
    year_last
from {{ source('raw', 'climbers') }}