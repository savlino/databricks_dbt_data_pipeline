select
    grade_id,
    grade_fra
from {{ source('raw', 'grades') }}