-- Intermediate model: Player home divisions
-- Determines each player's primary division based on where they play most frequently
-- Used for calculating cross-division matchup awards (e.g., giant killing)

with player_division_appearances as (
    select
        player_name,
        division,
        count(*) as rubbers_played
    from {{ ref('int_player_match_rubbers') }}
    group by player_name, division
),

player_primary_division as (
    select
        player_name,
        division as home_division,
        rubbers_played,
        row_number() over (partition by player_name order by rubbers_played desc, division) as rn
    from player_division_appearances
),

extract_division_info as (
    select
        player_name,
        home_division,
        rubbers_played,
        
        -- Extract division category (Open, Womens, Mixed, Mens)
        case
            when home_division like '%Open%' then 'Open'
            when home_division like '%Womens%' then 'Womens'
            when home_division like '%Mixed%' then 'Mixed'
            when home_division like '%Mens%' then 'Mens'
            else 'Unknown'
        end as division_category,
        
        -- Extract division number (lower number = higher division)
        -- Premier divisions treated as 0 (highest)
        case
            when home_division like '%Premier%' then 0
            else cast(regexp_extract(home_division, 'Division (\d+)', 1) as integer)
        end as home_division_number
        
    from player_primary_division
    where rn = 1
)

select
    player_name,
    home_division,
    division_category,
    home_division_number,
    rubbers_played as rubbers_in_home_division
from extract_division_info
