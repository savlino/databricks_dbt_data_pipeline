with climbers as (
    select *
    from {{ ref('int_climbers_transformed') }}
    where country is not null
      and sex is not null
      and grade_numeric is not null
),

stats as (
    select
        country,
        sex,
        count(distinct user_id) as climber_count,
        round(avg(age), 1) as avg_age,
        round(avg(grade_numeric), 2) as avg_grade_numeric,
        percentile_approx(height, 0.5) as median_height,
        max(grade_numeric) as max_grade_numeric
    from climbers
    group by country, sex
),

max_grade_details as (
    select
        climbers.country,
        climbers.sex,
        max(climbers.grade_label) as max_grade_label,
        count(distinct climbers.user_id) as max_grade_climber_count
    from climbers
    inner join stats
        on climbers.country = stats.country
       and climbers.sex = stats.sex
       and climbers.grade_numeric = stats.max_grade_numeric
    group by climbers.country, climbers.sex
)

select
    stats.country,
    stats.sex,
    stats.climber_count,
    stats.avg_age,
    stats.avg_grade_numeric,
    stats.median_height,
    stats.max_grade_numeric,
    max_grade_details.max_grade_label,
    max_grade_details.max_grade_climber_count
from stats
inner join max_grade_details
    on stats.country = max_grade_details.country
   and stats.sex = max_grade_details.sex