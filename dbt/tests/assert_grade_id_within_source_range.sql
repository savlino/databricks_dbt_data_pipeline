with grade_range as (
    select
        min(grade_id) as min_grade_id,
        max(grade_id) as max_grade_id
    from {{ ref('stg_grades') }}
)

select
    climbers.user_id,
    climbers.grade_numeric
from {{ ref('int_climbers_transformed') }} as climbers
cross join grade_range
where climbers.grade_numeric < grade_range.min_grade_id
   or climbers.grade_numeric > grade_range.max_grade_id