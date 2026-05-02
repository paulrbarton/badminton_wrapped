-- Intermediate model: Player highest divisions
-- Determines each player's highest division (most competitive level) they have played in
-- Used for calculating cross-division matchup awards (e.g., giant killing)
-- Lower division number = higher skill level (0 = Premier, 1 = Division 1, etc.)

with player_division_appearances as (
    select
        player_name,
        division,
        season,
        count(*) as rubbers_played
    from {{ ref('int_player_match_rubbers') }}
    group by player_name, division, season
),

extract_division_info as (
    select
        player_name,
        division,
        season,
        rubbers_played,
        
        -- Extract division category (Open, Womens, Mixed, Mens)
        case
            when division like '%Open%' then 'Open'
            when division like '%Womens%' then 'Womens'
            when division like '%Mixed%' then 'Mixed'
            when division like '%Mens%' then 'Mens'
            else 'Unknown'
        end as division_category,
        
        -- Extract division number (lower number = higher division)
        -- Premier divisions treated as 0 (highest)
        case
            when division like '%Premier%' then 0
            else cast(regexp_extract(division, 'Division (\d+)', 1) as integer)
        end as division_number
        
    from player_division_appearances
),

player_highest_division as (
    select
        player_name,
        division_category,
        season,
        min(division_number) as highest_division_number  -- Minimum = highest level
    from extract_division_info
    group by player_name, division_category, season
),

-- Get the full division name for the highest division
with_division_name as (
    select
        phd.player_name,
        phd.division_category,
        phd.season,
        phd.highest_division_number,
        edi.division as highest_division,
        edi.rubbers_played as rubbers_in_highest_division
    from player_highest_division phd
    inner join extract_division_info edi
        on phd.player_name = edi.player_name
        and phd.division_category = edi.division_category
        and phd.highest_division_number = edi.division_number
        and phd.season = edi.season
),

-- Handle players who played in multiple categories - select primary category
final as (
    select
        player_name,
        highest_division,
        division_category,
        highest_division_number,
        rubbers_in_highest_division,
        season,
        row_number() over (partition by player_name, season order by rubbers_in_highest_division desc, highest_division_number) as rn
    from with_division_name
)

select
    player_name,
    highest_division,
    division_category,
    highest_division_number,
    rubbers_in_highest_division,
    season
from final
where rn = 1
