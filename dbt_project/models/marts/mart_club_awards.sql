-- Mart model: Club awards by player
-- Aggregates various awards (most comebacks, etc.) by player and club
-- Each row represents one player winning one award

with comeback_rubbers as (
    -- Identify rubbers where a player came back from losing game 1
    -- A comeback is: lost game 1, but won the rubber (meaning won games 2 and 3)
    select
        player_name,
        -- Extract club name (everything before " Open", " Womens", " Mixed", etc.)
        trim(regexp_replace(team, ' (Open|Womens|Mixed|Mens) \d+.*$', '')) as club,
        match_id,
        rubber_number
    from {{ ref('int_player_match_rubbers') }}
    where 
        -- Must have gone to 3 games (otherwise no comeback possible)
        went_to_three_games = true
        -- Lost game 1
        and game_1_won = false
        -- But won the rubber (meaning won games 2 and 3)
        and won_rubber = true
        -- Exclude forfeits
        and is_forfeit = false
),

comeback_counts as (
    -- Count comebacks per player and club
    select
        player_name,
        club,
        count(*) as comeback_count
    from comeback_rubbers
    group by 
        player_name,
        club
),

comeback_awards as (
    -- Format as award, keeping only the top player per club
    select
        'most_comebacks' as award,
        club,
        player_name as player,
        comeback_count as award_value,
        row_number() over (partition by club order by comeback_count desc, player_name) as rn
    from comeback_counts
),

comeback_details as (
    -- Gather detailed information for each comeback rubber
    select
        pmr.player_name,
        trim(regexp_replace(pmr.team, ' (Open|Womens|Mixed|Mens) \d+.*$', '')) as club,
        pmr.match_date,
        pmr.opponent_team,
        pmr.partner_name,
        pmr.rubber_number,
        pmr.game_1_score_for,
        pmr.game_1_score_against,
        pmr.game_2_score_for,
        pmr.game_2_score_against,
        pmr.game_3_score_for,
        pmr.game_3_score_against,
        pmr.venue
    from {{ ref('int_player_match_rubbers') }} pmr
    inner join comeback_awards ca
        on pmr.player_name = ca.player
        and trim(regexp_replace(pmr.team, ' (Open|Womens|Mixed|Mens) \d+.*$', '')) = ca.club
        and ca.rn = 1  -- Only get details for award winners
    where 
        -- Apply same comeback logic
        pmr.went_to_three_games = true
        and pmr.game_1_won = false
        and pmr.won_rubber = true
        and pmr.is_forfeit = false
),

comeback_details_formatted as (
    -- Format each rubber detail as a readable string
    select
        player_name,
        club,
        match_date || ': vs ' || opponent_team || 
        ' (Rubber ' || rubber_number || ' with ' || partner_name || ') - ' ||
        'Lost Game 1 ' || game_1_score_for || '-' || game_1_score_against || ', ' ||
        'Won Game 2 ' || game_2_score_for || '-' || game_2_score_against || ', ' ||
        'Won Game 3 ' || game_3_score_for || '-' || game_3_score_against as detail_line
    from comeback_details
    order by 
        player_name,
        club,
        match_date,
        rubber_number
),

comeback_details_aggregated as (
    -- Aggregate all details into a single text field per player/club
    select
        player_name,
        club,
        string_agg(detail_line, ' | ') as award_details
    from comeback_details_formatted
    group by 
        player_name,
        club
),

stalwart_stats as (
    -- Calculate match and rubber counts per player/club
    select
        player_name,
        trim(regexp_replace(team, ' (Open|Womens|Mixed|Mens) \d+.*$', '')) as club,
        count(distinct match_id) as matches_played,
        count(*) as rubbers_played,
        sum(total_points_for + total_points_against) as total_points
    from {{ ref('int_player_match_rubbers') }}
    where is_forfeit = false
    group by 
        player_name,
        trim(regexp_replace(team, ' (Open|Womens|Mixed|Mens) \d+.*$', ''))
),

stalwart_awards as (
    -- Format as award, keeping only the top player per club
    select
        'club_stalwart' as award,
        club,
        player_name as player,
        matches_played as award_value,
        rubbers_played,
        total_points,
        row_number() over (partition by club order by matches_played desc, rubbers_played desc, player_name) as rn
    from stalwart_stats
),

stalwart_details as (
    -- Create award details text
    select
        player,
        club,
        'Played in ' || award_value || ' matches | ' ||
        'Played ' || rubbers_played || ' rubbers | ' ||
        'Total points: ' || total_points as award_details
    from stalwart_awards
    where rn = 1
),

comeback_final as (
    select
        ca.award,
        ca.club,
        ca.player,
        ca.award_value,
        coalesce(cda.award_details, '') as award_details
    from comeback_awards ca
    left join comeback_details_aggregated cda
        on ca.player = cda.player_name
        and ca.club = cda.club
    where ca.rn = 1
),

stalwart_final as (
    select
        sa.award,
        sa.club,
        sa.player,
        sa.award_value,
        sd.award_details
    from stalwart_awards sa
    left join stalwart_details sd
        on sa.player = sd.player
        and sa.club = sd.club
    where sa.rn = 1
),

no_mercy_rubbers as (
    -- Find 2-game wins with biggest margins
    select
        match_id,
        rubber_number,
        home_team,
        away_team,
        home_player_1,
        home_player_2,
        away_player_1,
        away_player_2,
        rubber_winner,
        rubber_score,
        game_1_margin,
        game_2_margin,
        -- Maximum margin from either game
        greatest(game_1_margin, game_2_margin) as max_margin
    from {{ ref('int_match_rubbers') }}
    where 
        -- Only 2-game wins (not 3)
        went_to_three_games = false
        -- Must be a completed rubber with winner
        and rubber_winner in ('home', 'away')
        -- Exclude forfeits
        and is_forfeit = false
),

no_mercy_partnerships as (
    -- Identify the winning partnership (both players)
    select
        -- Player 1
        case 
            when rubber_winner = 'home' then home_player_1
            else away_player_1
        end as player_1,
        -- Player 2
        case 
            when rubber_winner = 'home' then home_player_2
            else away_player_2
        end as player_2,
        -- Winning team
        case 
            when rubber_winner = 'home' then home_team
            else away_team
        end as team,
        -- Opponent team
        case 
            when rubber_winner = 'home' then away_team
            else home_team
        end as opponent_team,
        -- Club extraction
        trim(regexp_replace(
            case when rubber_winner = 'home' then home_team else away_team end,
            ' (Open|Womens|Mixed|Mens) \d+.*$', 
            ''
        )) as club,
        max_margin,
        rubber_score,
        match_id,
        rubber_number
    from no_mercy_rubbers
),

no_mercy_top_partnerships as (
    -- Find the biggest margin per club
    select
        club,
        player_1,
        player_2,
        team,
        opponent_team,
        max_margin,
        rubber_score,
        row_number() over (partition by club order by max_margin desc, player_1, player_2) as rn
    from no_mercy_partnerships
),

no_mercy_details as (
    -- Create details for both players
    select
        club,
        player_1,
        player_2,
        'Team: ' || team || ' | ' ||
        'vs ' || opponent_team || ' | ' ||
        'Score: ' || rubber_score as award_details,
        max_margin
    from no_mercy_top_partnerships
    where rn = 1
),

no_mercy_awards as (
    -- Create award row for the partnership with both players
    select
        'no_mercy' as award,
        club,
        player_1 as player,
        player_2,
        max_margin as award_value,
        award_details
    from no_mercy_details
)

select 
    award,
    club,
    player,
    null as player_2,
    award_value,
    award_details
from comeback_final

union all

select 
    award,
    club,
    player,
    null as player_2,
    award_value,
    award_details
from stalwart_final

union all

select 
    award,
    club,
    player,
    player_2,
    award_value,
    award_details
from no_mercy_awards

order by 
    award_value desc,
    club
