select
    climbers.user_id,
    climbers.country,
    case
        when climbers.sex = 0 then 'M'
        when climbers.sex = 1 then 'F'
        else cast(climbers.sex as string)
    end as sex,
    climbers.height,
    climbers.weight,
    climbers.age,
    climbers.years_cl,
    cast(climbers.date_first as date) as date_first,
    cast(climbers.date_last as date) as date_last,
    climbers.grades_count,
    climbers.grades_first,
    climbers.grades_last,
    climbers.grades_max,
    climbers.grades_mean,
    climbers.year_first,
    climbers.year_last,
    grades.grade_id as grade_numeric,
    grades.grade_fra as grade_label
from {{ ref('stg_climbers') }} as climbers
inner join {{ ref('stg_grades') }} as grades
    on climbers.grades_max = grades.grade_id