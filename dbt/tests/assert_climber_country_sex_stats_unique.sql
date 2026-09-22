select
    country,
    sex
from {{ ref('climber_country_sex_stats') }}
group by country, sex
having count(*) > 1