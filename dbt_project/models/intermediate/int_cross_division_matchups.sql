-- Intermediate model: Cross-division matchup results
-- Identifies rubbers where a player defeated an opponent from a higher division
-- Based on each player's highest division played (most competitive level achieved)

with player_rubbers as (
    select
        match_id,
        rubber_number,
        player_name,
        partner_name,
        opponent_1,
        opponent_2,
        team,
        opponent_team,
        division as match_division,
        match_date,
        venue,
        won_rubber,
        
        -- Winning margin across all games in the rubber
        total_points_for - total_points_against as rubber_margin
        
    from {{ ref('int_player_match_rubbers') }}
    where won_rubber = true  -- Only interested in wins for giant killing award
),

player_highest_divs as (
    select
        player_name,
        highest_division,
        division_category,
        highest_division_number
    from {{ ref('int_player_highest_divisions') }}
),

-- Join player with their highest division
players_with_highest_div as (
    select
        pr.*,
        phd.highest_division as player_highest_division,
        phd.division_category as player_division_category,
        phd.highest_division_number as player_highest_division_number
    from player_rubbers pr
    left join player_highest_divs phd
        on pr.player_name = phd.player_name
),

-- Get highest divisions for both opponents
with_opponent_divs as (
    select
        pwhd.*,
        
        -- Opponent 1 highest division
        opp1.highest_division as opponent_1_highest_division,
        opp1.division_category as opponent_1_division_category,
        opp1.highest_division_number as opponent_1_highest_division_number,
        
        -- Opponent 2 highest division
        opp2.highest_division as opponent_2_highest_division,
        opp2.division_category as opponent_2_division_category,
        opp2.highest_division_number as opponent_2_highest_division_number
        
    from players_with_highest_div pwhd
    left join player_highest_divs opp1
        on pwhd.opponent_1 = opp1.player_name
    left join player_highest_divs opp2
        on pwhd.opponent_2 = opp2.player_name
),

-- Identify the higher-division opponent (if any)
identify_giant_killings as (
    select
        *,
        
        -- Check opponent 1: same category and higher division (lower number)
        case
            when opponent_1_division_category = player_division_category
                and opponent_1_highest_division_number < player_highest_division_number
            then true
            else false
        end as opponent_1_is_higher_division,
        
        -- Check opponent 2: same category and higher division (lower number)
        case
            when opponent_2_division_category = player_division_category
                and opponent_2_highest_division_number < player_highest_division_number
            then true
            else false
        end as opponent_2_is_higher_division,
        
        -- Calculate division gap for each opponent
        case
            when opponent_1_division_category = player_division_category
                and opponent_1_highest_division_number < player_highest_division_number
            then player_highest_division_number - opponent_1_highest_division_number
            else 0
        end as opponent_1_division_gap,
        
        case
            when opponent_2_division_category = player_division_category
                and opponent_2_highest_division_number < player_highest_division_number
            then player_highest_division_number - opponent_2_highest_division_number
            else 0
        end as opponent_2_division_gap
        
    from with_opponent_divs
),

-- Select the higher-division opponent (use the one with bigger gap)
final as (
    select
        match_id,
        rubber_number,
        player_name,
        partner_name,
        team,
        opponent_team,
        match_division,
        match_date,
        venue,
        player_highest_division,
        player_division_category,
        player_highest_division_number,
        rubber_margin,
        
        -- Select the opponent with higher division (bigger gap)
        case
            when opponent_1_division_gap >= opponent_2_division_gap then opponent_1
            else opponent_2
        end as higher_division_opponent_name,
        
        case
            when opponent_1_division_gap >= opponent_2_division_gap then opponent_1_highest_division
            else opponent_2_highest_division
        end as higher_division_opponent_highest_division,
        
        case
            when opponent_1_division_gap >= opponent_2_division_gap then opponent_1_highest_division_number
            else opponent_2_highest_division_number
        end as higher_division_opponent_division_number,
        
        -- The actual division gap (how many divisions higher)
        greatest(opponent_1_division_gap, opponent_2_division_gap) as divisions_higher
        
    from identify_giant_killings
    where opponent_1_is_higher_division = true
        or opponent_2_is_higher_division = true  -- At least one opponent from higher division
)

select * from final
