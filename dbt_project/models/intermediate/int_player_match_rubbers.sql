-- Intermediate model: Individual player statistics for each match rubber
-- Unpivots int_match_rubbers to show each player's rubber performance
-- Each row represents one player in one rubber

with home_players as (
    -- Home team player 1
    select
        match_id,
        rubber_number,
        home_team as team,
        away_team as opponent_team,
        home_player_1 as player_name,
        home_player_2 as partner_name,
        away_player_1 as opponent_1,
        away_player_2 as opponent_2,
        match_date,
        division,
        venue,
        'home' as home_away,
        1 as player_position,
        
        -- Rubber outcome from player's perspective
        rubber_winner,
        case when rubber_winner = 'home' then true else false end as won_rubber,
        
        -- Game scores
        total_games_in_rubber,
        home_games_won as games_won,
        away_games_won as games_lost,
        
        -- Game 1
        game_1_home_score as game_1_score_for,
        game_1_away_score as game_1_score_against,
        case when game_1_winner = 'home' then true else false end as game_1_won,
        game_1_margin,
        game_1_went_to_deuce,
        
        -- Game 2
        game_2_home_score as game_2_score_for,
        game_2_away_score as game_2_score_against,
        case when game_2_winner = 'home' then true else false end as game_2_won,
        game_2_margin,
        game_2_went_to_deuce,
        
        -- Game 3
        game_3_home_score as game_3_score_for,
        game_3_away_score as game_3_score_against,
        case when game_3_winner = 'home' then true else false end as game_3_won,
        game_3_margin,
        game_3_went_to_deuce,
        
        -- Other metadata
        went_to_three_games,
        rubber_score,
        is_forfeit
        
    from {{ ref('int_match_rubbers') }}
    where home_player_1 is not null
    
    union all
    
    -- Home team player 2
    select
        match_id,
        rubber_number,
        home_team as team,
        away_team as opponent_team,
        home_player_2 as player_name,
        home_player_1 as partner_name,
        away_player_1 as opponent_1,
        away_player_2 as opponent_2,
        match_date,
        division,
        venue,
        'home' as home_away,
        2 as player_position,
        
        rubber_winner,
        case when rubber_winner = 'home' then true else false end as won_rubber,
        
        total_games_in_rubber,
        home_games_won as games_won,
        away_games_won as games_lost,
        
        game_1_home_score as game_1_score_for,
        game_1_away_score as game_1_score_against,
        case when game_1_winner = 'home' then true else false end as game_1_won,
        game_1_margin,
        game_1_went_to_deuce,
        
        game_2_home_score as game_2_score_for,
        game_2_away_score as game_2_score_against,
        case when game_2_winner = 'home' then true else false end as game_2_won,
        game_2_margin,
        game_2_went_to_deuce,
        
        game_3_home_score as game_3_score_for,
        game_3_away_score as game_3_score_against,
        case when game_3_winner = 'home' then true else false end as game_3_won,
        game_3_margin,
        game_3_went_to_deuce,
        
        went_to_three_games,
        rubber_score,
        is_forfeit
        
    from {{ ref('int_match_rubbers') }}
    where home_player_2 is not null
),

away_players as (
    -- Away team player 1
    select
        match_id,
        rubber_number,
        away_team as team,
        home_team as opponent_team,
        away_player_1 as player_name,
        away_player_2 as partner_name,
        home_player_1 as opponent_1,
        home_player_2 as opponent_2,
        match_date,
        division,
        venue,
        'away' as home_away,
        1 as player_position,
        
        rubber_winner,
        case when rubber_winner = 'away' then true else false end as won_rubber,
        
        total_games_in_rubber,
        away_games_won as games_won,
        home_games_won as games_lost,
        
        game_1_away_score as game_1_score_for,
        game_1_home_score as game_1_score_against,
        case when game_1_winner = 'away' then true else false end as game_1_won,
        game_1_margin,
        game_1_went_to_deuce,
        
        game_2_away_score as game_2_score_for,
        game_2_home_score as game_2_score_against,
        case when game_2_winner = 'away' then true else false end as game_2_won,
        game_2_margin,
        game_2_went_to_deuce,
        
        game_3_away_score as game_3_score_for,
        game_3_home_score as game_3_score_against,
        case when game_3_winner = 'away' then true else false end as game_3_won,
        game_3_margin,
        game_3_went_to_deuce,
        
        went_to_three_games,
        rubber_score,
        is_forfeit
        
    from {{ ref('int_match_rubbers') }}
    where away_player_1 is not null
    
    union all
    
    -- Away team player 2
    select
        match_id,
        rubber_number,
        away_team as team,
        home_team as opponent_team,
        away_player_2 as player_name,
        away_player_1 as partner_name,
        home_player_1 as opponent_1,
        home_player_2 as opponent_2,
        match_date,
        division,
        venue,
        'away' as home_away,
        2 as player_position,
        
        rubber_winner,
        case when rubber_winner = 'away' then true else false end as won_rubber,
        
        total_games_in_rubber,
        away_games_won as games_won,
        home_games_won as games_lost,
        
        game_1_away_score as game_1_score_for,
        game_1_home_score as game_1_score_against,
        case when game_1_winner = 'away' then true else false end as game_1_won,
        game_1_margin,
        game_1_went_to_deuce,
        
        game_2_away_score as game_2_score_for,
        game_2_home_score as game_2_score_against,
        case when game_2_winner = 'away' then true else false end as game_2_won,
        game_2_margin,
        game_2_went_to_deuce,
        
        game_3_away_score as game_3_score_for,
        game_3_home_score as game_3_score_against,
        case when game_3_winner = 'away' then true else false end as game_3_won,
        game_3_margin,
        game_3_went_to_deuce,
        
        went_to_three_games,
        rubber_score,
        is_forfeit
        
    from {{ ref('int_match_rubbers') }}
    where away_player_2 is not null
),

final as (
    select
        match_id,
        rubber_number,
        player_name,
        partner_name,
        team,
        opponent_team,
        opponent_1,
        opponent_2,
        match_date,
        division,
        venue,
        home_away,
        player_position,
        
        -- Rubber outcome
        won_rubber,
        rubber_winner,
        
        -- Games performance
        total_games_in_rubber,
        games_won,
        games_lost,
        went_to_three_games,
        
        -- Individual game details
        game_1_score_for,
        game_1_score_against,
        game_1_won,
        game_1_margin,
        game_1_went_to_deuce,
        
        game_2_score_for,
        game_2_score_against,
        game_2_won,
        game_2_margin,
        game_2_went_to_deuce,
        
        game_3_score_for,
        game_3_score_against,
        game_3_won,
        game_3_margin,
        game_3_went_to_deuce,
        
        -- Raw score for reference
        rubber_score,
        
        -- Total points scored
        game_1_score_for + 
        coalesce(game_2_score_for, 0) + 
        coalesce(game_3_score_for, 0) as total_points_for,
        
        game_1_score_against + 
        coalesce(game_2_score_against, 0) + 
        coalesce(game_3_score_against, 0) as total_points_against,
        
        -- Point differential
        (game_1_score_for + coalesce(game_2_score_for, 0) + coalesce(game_3_score_for, 0)) -
        (game_1_score_against + coalesce(game_2_score_against, 0) + coalesce(game_3_score_against, 0)) as point_differential,
        
        -- Forfeit flag
        is_forfeit
        
    from (
        select * from home_players
        union all
        select * from away_players
    )
)

select * from final
