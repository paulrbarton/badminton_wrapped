-- Fails if a club receives the same award category more than once in a season.
select
    season,
    club,
    award,
    count(*) as award_count
from {{ ref('mart_club_awards') }}
group by
    season,
    club,
    award
having count(*) > 1
