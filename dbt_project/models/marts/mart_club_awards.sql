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
        game_1_margin + game_2_margin as total_margin
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
        total_margin,
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
        total_margin,
        rubber_score,
        row_number() over (partition by club order by total_margin desc, player_1, player_2) as rn
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
        total_margin
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
        total_margin as award_value,
        award_details
    from no_mercy_details
),

-- ============================================================================
-- PERFORMS UNDER PRESSURE AWARD
-- Player who won the most games with a 2-point margin of victory
-- ============================================================================

pressure_games as (
    -- Identify all games won by exactly 2 points
    select
        player_name,
        trim(regexp_replace(team, ' (Open|Womens|Mixed|Mens) \d+.*$', '')) as club,
        match_id,
        rubber_number,
        match_date,
        opponent_team,
        partner_name,
        -- Game 1 details
        case 
            when game_1_won = true and game_1_margin = 2 
            then 'Game 1: ' || game_1_score_for || '-' || game_1_score_against
            else null 
        end as game_1_detail,
        -- Game 2 details
        case 
            when game_2_won = true and game_2_margin = 2 
            then 'Game 2: ' || game_2_score_for || '-' || game_2_score_against
            else null 
        end as game_2_detail,
        -- Game 3 details
        case 
            when game_3_won = true and game_3_margin = 2 
            then 'Game 3: ' || game_3_score_for || '-' || game_3_score_against
            else null 
        end as game_3_detail
    from {{ ref('int_player_match_rubbers') }}
    where 
        is_forfeit = false
        and (
            (game_1_won = true and game_1_margin = 2) or
            (game_2_won = true and game_2_margin = 2) or
            (game_3_won = true and game_3_margin = 2)
        )
),

pressure_games_counted as (
    -- Count 2-point wins per player (each game counted separately)
    select
        player_name,
        club,
        -- Count each game individually
        sum(case when game_1_detail is not null then 1 else 0 end) +
        sum(case when game_2_detail is not null then 1 else 0 end) +
        sum(case when game_3_detail is not null then 1 else 0 end) as pressure_wins
    from pressure_games
    group by 
        player_name,
        club
),

pressure_top_player as (
    -- Find top player per club
    select
        club,
        player_name,
        pressure_wins,
        row_number() over (partition by club order by pressure_wins desc, player_name) as rn
    from pressure_games_counted
),

pressure_details as (
    -- Get detailed list of pressure wins for award winners
    select
        pg.player_name,
        pg.club,
        pg.match_date || ': vs ' || pg.opponent_team || 
        ' (Rubber ' || pg.rubber_number || ' with ' || pg.partner_name || ') - ' ||
        coalesce(pg.game_1_detail, '') || 
        case when pg.game_1_detail is not null and (pg.game_2_detail is not null or pg.game_3_detail is not null) then ', ' else '' end ||
        coalesce(pg.game_2_detail, '') ||
        case when pg.game_2_detail is not null and pg.game_3_detail is not null then ', ' else '' end ||
        coalesce(pg.game_3_detail, '') as detail_line
    from pressure_games pg
    inner join pressure_top_player ptp
        on pg.player_name = ptp.player_name
        and pg.club = ptp.club
        and ptp.rn = 1
    order by 
        pg.player_name,
        pg.club,
        pg.match_date,
        pg.rubber_number
),

pressure_details_aggregated as (
    -- Aggregate all details into a single text field per player/club
    select
        player_name,
        club,
        string_agg(detail_line, ' | ') as award_details
    from pressure_details
    group by 
        player_name,
        club
),

pressure_final as (
    -- Final pressure award with details
    select
        'performs_under_pressure' as award,
        ptp.club,
        ptp.player_name as player,
        ptp.pressure_wins as award_value,
        coalesce(pda.award_details, 'No details available') as award_details
    from pressure_top_player ptp
    left join pressure_details_aggregated pda
        on ptp.player_name = pda.player_name
        and ptp.club = pda.club
    where ptp.rn = 1
),

-- ============================================================================
-- LONGEST WINNING STREAK AWARD
-- Player who won the most consecutive rubbers
-- ============================================================================

player_rubbers_chronological as (
    -- Get all rubbers for each player in chronological order
    select
        player_name,
        trim(regexp_replace(team, ' (Open|Womens|Mixed|Mens) \d+.*$', '')) as club,
        match_id,
        rubber_number,
        match_date,
        opponent_team,
        partner_name,
        won_rubber,
        is_forfeit,
        -- Create a chronological ordering
        row_number() over (
            partition by player_name, trim(regexp_replace(team, ' (Open|Womens|Mixed|Mens) \d+.*$', ''))
            order by match_date, match_id, rubber_number
        ) as rubber_seq
    from {{ ref('int_player_match_rubbers') }}
    where is_forfeit = false  -- Exclude forfeits
),

streak_groups as (
    -- Identify streak groups by subtracting sequence numbers
    -- When wins are consecutive, this difference stays constant
    select
        player_name,
        club,
        match_id,
        rubber_number,
        match_date,
        opponent_team,
        partner_name,
        won_rubber,
        rubber_seq,
        -- Group identifier: when won_rubber changes, this creates a new group
        rubber_seq - row_number() over (
            partition by player_name, club, won_rubber
            order by rubber_seq
        ) as streak_group
    from player_rubbers_chronological
),

winning_streaks as (
    -- Count consecutive wins in each streak group
    select
        player_name,
        club,
        streak_group,
        count(*) as streak_length,
        min(match_date) as streak_start_date,
        max(match_date) as streak_end_date,
        -- Collect rubber details for the streak
        string_agg(
            match_date || ': vs ' || opponent_team || ' (Rubber ' || rubber_number || ' with ' || partner_name || ')',
            ' | '
            order by rubber_seq
        ) as streak_details
    from streak_groups
    where won_rubber = true  -- Only count winning streaks
    group by 
        player_name,
        club,
        streak_group
),

longest_streak_per_player as (
    -- Find the longest streak for each player/club combination
    select
        player_name,
        club,
        max(streak_length) as longest_streak,
        -- Get details of the longest streak (take first if tied)
        (array_agg(streak_details order by streak_length desc, streak_start_date))[1] as streak_details
    from winning_streaks
    group by 
        player_name,
        club
),

longest_streak_per_club as (
    -- Find the top player per club
    select
        club,
        player_name,
        longest_streak,
        streak_details,
        row_number() over (partition by club order by longest_streak desc, player_name) as rn
    from longest_streak_per_player
),

streak_final as (
    -- Final streak award
    select
        'longest_winning_streak' as award,
        club,
        player_name as player,
        longest_streak as award_value,
        streak_details as award_details
    from longest_streak_per_club
    where rn = 1
),

-- ============================================================================
-- DEFENSIVE WALL AWARD
-- Player who conceded the fewest points per rubber (best defense)
-- ============================================================================

defensive_stats as (
    -- Calculate total points conceded per player
    select
        player_name,
        trim(regexp_replace(team, ' (Open|Womens|Mixed|Mens) \d+.*$', '')) as club,
        count(*) as rubbers_played,
        sum(
            coalesce(game_1_score_against, 0) + 
            coalesce(game_2_score_against, 0) + 
            coalesce(game_3_score_against, 0)
        ) as total_points_conceded,
        -- Calculate average points conceded per rubber
        cast(sum(
            coalesce(game_1_score_against, 0) + 
            coalesce(game_2_score_against, 0) + 
            coalesce(game_3_score_against, 0)
        ) as decimal(10,2)) / count(*) as avg_points_conceded_per_rubber
    from {{ ref('int_player_match_rubbers') }}
    where 
        is_forfeit = false
        -- Only count players with significant playing time (at least 10 rubbers)
        and player_name in (
            select player_name
            from {{ ref('int_player_match_rubbers') }}
            where is_forfeit = false
            group by player_name
            having count(*) >= 10
        )
    group by 
        player_name,
        trim(regexp_replace(team, ' (Open|Womens|Mixed|Mens) \d+.*$', ''))
),

defensive_top_per_club as (
    -- Find player with lowest average points conceded per club
    select
        club,
        player_name,
        rubbers_played,
        total_points_conceded,
        avg_points_conceded_per_rubber,
        row_number() over (partition by club order by avg_points_conceded_per_rubber asc, player_name) as rn
    from defensive_stats
),

defensive_final as (
    -- Final defensive wall award
    select
        'defensive_wall' as award,
        club,
        player_name as player,
        -- Award value is the average (rounded to 1 decimal for display)
        cast(round(avg_points_conceded_per_rubber, 1) as int) as award_value,
        'Conceded ' || total_points_conceded || ' points across ' || rubbers_played || 
        ' rubbers (avg: ' || round(avg_points_conceded_per_rubber, 1) || ' points per rubber)' as award_details
    from defensive_top_per_club
    where rn = 1
),

giant_killing_stats as (
    -- Aggregate per player: max division gap and total margin across all giant killings
    -- Extract club directly in aggregation to reduce memory
    select
        player_name,
        trim(regexp_replace(team, ' (Open|Womens|Mixed|Mens) \d+.*$', '')) as club,
        max(divisions_higher) as max_divisions_higher,
        sum(rubber_margin) as total_margin,
        count(*) as giant_killing_count
    from {{ ref('int_cross_division_matchups') }}
    group by 
        player_name,
        trim(regexp_replace(team, ' (Open|Womens|Mixed|Mens) \d+.*$', ''))
),

giant_killing_awards as (
    -- Rank and select top player per club
    select
        'giant_killing' as award,
        club,
        player_name as player,
        max_divisions_higher as award_value,
        total_margin,
        giant_killing_count,
        row_number() over (partition by club order by max_divisions_higher desc, total_margin desc, player_name) as rn
    from giant_killing_stats
),

giant_killing_winners as (
    -- Filter to only award winners BEFORE joining to details
    select
        club,
        player
    from giant_killing_awards
    where rn = 1
),

giant_killing_details as (
    -- Get details only for award winners (much smaller result set)
    select
        cdm.player_name,
        trim(regexp_replace(cdm.team, ' (Open|Womens|Mixed|Mens) \d+.*$', '')) as club,
        cdm.match_date || ': vs ' || cdm.opponent_team || 
        ' (Rubber ' || cdm.rubber_number || ' with ' || cdm.partner_name || ') - ' ||
        'Defeated ' || cdm.higher_division_opponent_name || 
        ' from ' || cdm.higher_division_opponent_highest_division || 
        ' (' || cdm.divisions_higher || ' division' || case when cdm.divisions_higher > 1 then 's' else '' end || ' higher)' ||
        ', margin: +' || cdm.rubber_margin as detail_line,
        cdm.divisions_higher,
        cdm.match_date,
        cdm.rubber_number
    from {{ ref('int_cross_division_matchups') }} cdm
    inner join giant_killing_winners gkw
        on cdm.player_name = gkw.player
        and trim(regexp_replace(cdm.team, ' (Open|Womens|Mixed|Mens) \d+.*$', '')) = gkw.club
),

giant_killing_details_aggregated as (
    -- Aggregate all details into a single text field per player/club
    select
        player_name,
        club,
        string_agg(detail_line, ' | ' order by divisions_higher desc, match_date, rubber_number) as award_details
    from giant_killing_details
    group by 
        player_name,
        club
),

giant_killing_final as (
    select
        gka.award,
        gka.club,
        gka.player,
        gka.award_value,
        coalesce(gkda.award_details, '') as award_details
    from giant_killing_awards gka
    left join giant_killing_details_aggregated gkda
        on gka.player = gkda.player_name
        and gka.club = gkda.club
    where gka.rn = 1
),

-- ============================================================================
-- EPIC WIN AWARD
-- Pair that won a rubber while scoring the most total points
-- Must have scored more than 21 points in game 3
-- ============================================================================

epic_win_rubbers as (
    -- Find rubbers that went to 3 games where the winning pair scored >21 in game 3
    select
        match_id,
        rubber_number,
        home_team,
        away_team,
        home_player_1,
        home_player_2,
        away_player_1,
        away_player_2,
        match_date,
        venue,
        rubber_winner,
        rubber_score,
        -- Calculate total points for home team
        game_1_home_score + game_2_home_score + game_3_home_score as home_total_points,
        -- Calculate total points for away team
        game_1_away_score + game_2_away_score + game_3_away_score as away_total_points,
        -- Get game 3 scores
        game_3_home_score,
        game_3_away_score
    from {{ ref('int_match_rubbers') }}
    where 
        -- Must have gone to 3 games
        went_to_three_games = true
        -- Must have a winner
        and rubber_winner in ('home', 'away')
        -- Exclude forfeits
        and is_forfeit = false
        -- Winning team must have scored more than 21 in game 3
        and (
            (rubber_winner = 'home' and game_3_home_score > 21)
            or (rubber_winner = 'away' and game_3_away_score > 21)
        )
),

epic_win_partnerships as (
    -- Identify the winning partnership with their total points
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
        -- Total points scored by winning team
        case 
            when rubber_winner = 'home' then home_total_points
            else away_total_points
        end as total_points_scored,
        -- Game 3 score by winning team
        case 
            when rubber_winner = 'home' then game_3_home_score
            else game_3_away_score
        end as game_3_score,
        -- Club extraction
        trim(regexp_replace(
            case when rubber_winner = 'home' then home_team else away_team end,
            ' (Open|Womens|Mixed|Mens) \d+.*$', 
            ''
        )) as club,
        match_date,
        venue,
        rubber_score,
        match_id,
        rubber_number
    from epic_win_rubbers
),

epic_win_top_partnerships as (
    -- Find the highest total points scored per club
    select
        club,
        player_1,
        player_2,
        team,
        opponent_team,
        total_points_scored,
        game_3_score,
        match_date,
        venue,
        rubber_score,
        row_number() over (partition by club order by total_points_scored desc, game_3_score desc, player_1, player_2) as rn
    from epic_win_partnerships
),

epic_win_details as (
    -- Create details for both players
    select
        club,
        player_1,
        player_2,
        match_date || ' at ' || venue || ' vs ' || opponent_team || 
        ' (Score: ' || rubber_score || ', Total points: ' || total_points_scored || 
        ', Game 3: ' || game_3_score || ')' as award_details,
        total_points_scored
    from epic_win_top_partnerships
    where rn = 1
),

epic_win_awards as (
    -- Create award row for the partnership with both players
    select
        'epic_win' as award,
        club,
        player_1 as player,
        player_2,
        total_points_scored as award_value,
        award_details
    from epic_win_details
),

-- Clean Sweep Specialist: Most 2-0 rubber wins (minimum 3)
clean_sweep_rubbers as (
    -- Identify all 2-0 rubber wins
    select
        player_name,
        trim(regexp_replace(team, ' (Open|Womens|Mixed|Mens) \d+.*$', '')) as club,
        match_id,
        rubber_number,
        match_date,
        opponent_team,
        partner_name,
        venue,
        rubber_score
    from {{ ref('int_player_match_rubbers') }}
    where 
        is_forfeit = false
        and went_to_three_games = false  -- Only 2 games played
        and won_rubber = true             -- Player won the rubber
        and games_won = 2                 -- Won both games
),

clean_sweep_counted as (
    -- Count 2-0 wins per player and club
    select
        player_name,
        club,
        count(*) as clean_sweep_count
    from clean_sweep_rubbers
    group by 
        player_name,
        club
    having count(*) >= 3  -- Minimum threshold of 3 clean sweeps
),

clean_sweep_top_player as (
    -- Rank players per club
    select
        club,
        player_name,
        clean_sweep_count,
        row_number() over (partition by club order by clean_sweep_count desc, player_name) as rn
    from clean_sweep_counted
),

clean_sweep_details as (
    -- Gather detailed information for each clean sweep
    select
        csr.player_name,
        csr.club,
        csr.match_date || ': vs ' || csr.opponent_team || 
        ' (Rubber ' || csr.rubber_number || ' with ' || csr.partner_name || ') - ' ||
        'Won ' || csr.rubber_score as detail_line
    from clean_sweep_rubbers csr
    inner join clean_sweep_top_player cstp
        on csr.player_name = cstp.player_name
        and csr.club = cstp.club
        and cstp.rn = 1  -- Only get details for award winners
    order by 
        csr.player_name,
        csr.club,
        csr.match_date,
        csr.rubber_number
),

clean_sweep_details_aggregated as (
    -- Aggregate all details into a single text field
    select
        player_name,
        club,
        string_agg(detail_line, ' | ') as award_details
    from clean_sweep_details
    group by 
        player_name,
        club
),

clean_sweep_final as (
    -- Final award CTE
    select
        'clean_sweep_specialist' as award,
        cstp.club,
        cstp.player_name as player,
        cstp.clean_sweep_count as award_value,
        coalesce(csda.award_details, 'No details available') as award_details
    from clean_sweep_top_player cstp
    left join clean_sweep_details_aggregated csda
        on cstp.player_name = csda.player_name
        and cstp.club = csda.club
    where cstp.rn = 1
),

-- Perfect Partnership: Most 2-0 wins together (minimum 5 rubbers as a pair)
perfect_partnership_rubbers as (
    -- Identify all 2-0 rubber wins from match rubbers
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
        match_date,
        venue,
        rubber_score
    from {{ ref('int_match_rubbers') }}
    where 
        went_to_three_games = false  -- Only 2 games played
        and rubber_winner in ('home', 'away')  -- Completed rubber with winner
        and is_forfeit = false
),

perfect_partnership_partnerships as (
    -- Identify winning partnerships with normalized player ordering
    select
        -- Normalize partnership order alphabetically
        least(
            case when rubber_winner = 'home' then home_player_1 else away_player_1 end,
            case when rubber_winner = 'home' then home_player_2 else away_player_2 end
        ) as player_1,
        greatest(
            case when rubber_winner = 'home' then home_player_1 else away_player_1 end,
            case when rubber_winner = 'home' then home_player_2 else away_player_2 end
        ) as player_2,
        -- Team information
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
        match_id,
        rubber_number,
        match_date,
        venue,
        rubber_score
    from perfect_partnership_rubbers
),

perfect_partnership_counted as (
    -- Count 2-0 wins per partnership
    select
        club,
        player_1,
        player_2,
        count(*) as partnership_wins
    from perfect_partnership_partnerships
    group by 
        club,
        player_1,
        player_2
    having count(*) >= 5  -- Minimum threshold of 5 wins together
),

perfect_partnership_top_partnerships as (
    -- Rank partnerships per club
    select
        club,
        player_1,
        player_2,
        partnership_wins,
        row_number() over (partition by club order by partnership_wins desc, player_1, player_2) as rn
    from perfect_partnership_counted
),

perfect_partnership_details as (
    -- Gather detailed information, limited to first 5 matches
    select
        ppp.club,
        ppp.player_1,
        ppp.player_2,
        ppp.match_date || ': vs ' || ppp.opponent_team || 
        ' (Rubber ' || ppp.rubber_number || ') - Won ' || ppp.rubber_score as detail_line,
        row_number() over (
            partition by ppp.club, ppp.player_1, ppp.player_2 
            order by ppp.match_date, ppp.rubber_number
        ) as detail_rn
    from perfect_partnership_partnerships ppp
    inner join perfect_partnership_top_partnerships pptp
        on ppp.club = pptp.club
        and ppp.player_1 = pptp.player_1
        and ppp.player_2 = pptp.player_2
        and pptp.rn = 1  -- Only get details for award winners
),

perfect_partnership_details_aggregated as (
    -- Aggregate details with truncation
    select
        club,
        player_1,
        player_2,
        string_agg(
            detail_line, 
            ' | '
        ) || 
        case 
            when max(detail_rn) > 5 then 
                ' | ...and ' || (count(*) - 5)::varchar || ' more'
            else ''
        end as award_details
    from perfect_partnership_details
    where detail_rn <= 5  -- Limit to first 5 matches
    group by 
        club,
        player_1,
        player_2
),

perfect_partnership_awards as (
    -- Create award row for the partnership
    select
        'perfect_partnership' as award,
        pptp.club,
        pptp.player_1 as player,
        pptp.player_2,
        pptp.partnership_wins as award_value,
        coalesce(ppda.award_details, 'No details available') as award_details
    from perfect_partnership_top_partnerships pptp
    left join perfect_partnership_details_aggregated ppda
        on pptp.club = ppda.club
        and pptp.player_1 = ppda.player_1
        and pptp.player_2 = ppda.player_2
    where pptp.rn = 1
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

union all

select 
    award,
    club,
    player,
    null as player_2,
    award_value,
    award_details
from pressure_final

union all

select 
    award,
    club,
    player,
    null as player_2,
    award_value,
    award_details
from streak_final

union all

select 
    award,
    club,
    player,
    null as player_2,
    award_value,
    award_details
from defensive_final

union all

select 
    award,
    club,
    player,
    null as player_2,
    award_value,
    award_details
from giant_killing_final

union all

select 
    award,
    club,
    player,
    null as player_2,
    award_value,
    award_details
from clean_sweep_final

union all

select 
    award,
    club,
    player,
    player_2,
    award_value,
    award_details
from epic_win_awards

union all

select 
    award,
    club,
    player,
    player_2,
    award_value,
    award_details
from perfect_partnership_awards

order by 
    award_value desc,
    club
