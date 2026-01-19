-- Intermediate model: Parse rubber scores into individual games
-- Takes score strings like "21-11 21-10" or "17-21 21-16 18-21"
-- and breaks them into separate game records with winner determination
-- A badminton match has 9 rubbers (R1-R9)

with rubbers_unpivoted as (
    -- Unpivot rubbers R1-R9 from stg_games
    select
        match_id,
        home_team,
        away_team,
        match_date,
        division,
        venue,
        1 as rubber_number,
        R1_Home_P1 as home_player_1,
        R1_Home_P2 as home_player_2,
        R1_Away_P1 as away_player_1,
        R1_Away_P2 as away_player_2,
        R1_Score as rubber_score
    from {{ ref('stg_games') }}
    where R1_Score is not null
    
    union all
    
    select match_id, home_team, away_team, match_date, division, venue,
           2, R2_Home_P1, R2_Home_P2, R2_Away_P1, R2_Away_P2, R2_Score
    from {{ ref('stg_games') }}
    where R2_Score is not null
    
    union all
    
    select match_id, home_team, away_team, match_date, division, venue,
           3, R3_Home_P1, R3_Home_P2, R3_Away_P1, R3_Away_P2, R3_Score
    from {{ ref('stg_games') }}
    where R3_Score is not null
    
    union all
    
    select match_id, home_team, away_team, match_date, division, venue,
           4, R4_Home_P1, R4_Home_P2, R4_Away_P1, R4_Away_P2, R4_Score
    from {{ ref('stg_games') }}
    where R4_Score is not null
    
    union all
    
    select match_id, home_team, away_team, match_date, division, venue,
           5, R5_Home_P1, R5_Home_P2, R5_Away_P1, R5_Away_P2, R5_Score
    from {{ ref('stg_games') }}
    where R5_Score is not null
    
    union all
    
    select match_id, home_team, away_team, match_date, division, venue,
           6, R6_Home_P1, R6_Home_P2, R6_Away_P1, R6_Away_P2, R6_Score
    from {{ ref('stg_games') }}
    where R6_Score is not null
    
    union all
    
    select match_id, home_team, away_team, match_date, division, venue,
           7, R7_Home_P1, R7_Home_P2, R7_Away_P1, R7_Away_P2, R7_Score
    from {{ ref('stg_games') }}
    where R7_Score is not null
    
    union all
    
    select match_id, home_team, away_team, match_date, division, venue,
           8, R8_Home_P1, R8_Home_P2, R8_Away_P1, R8_Away_P2, R8_Score
    from {{ ref('stg_games') }}
    where R8_Score is not null
    
    union all
    
    select match_id, home_team, away_team, match_date, division, venue,
           9, R9_Home_P1, R9_Home_P2, R9_Away_P1, R9_Away_P2, R9_Score
    from {{ ref('stg_games') }}
    where R9_Score is not null
),

games_parsed as (
    -- Parse individual games from rubber scores
    -- Score format: "21-11 21-10" (2 games) or "17-21 21-16 18-21" (3 games)
    select
        match_id,
        home_team,
        away_team,
        match_date,
        division,
        venue,
        rubber_number,
        home_player_1,
        home_player_2,
        away_player_1,
        away_player_2,
        rubber_score,
        
        -- Split score string by spaces to get individual games
        string_split(rubber_score, ' ') as games_array,
        len(string_split(rubber_score, ' ')) as total_games_in_rubber,
        
        -- Parse game 1
        string_split(string_split(rubber_score, ' ')[1], '-')[1]::int as game_1_home_score,
        string_split(string_split(rubber_score, ' ')[1], '-')[2]::int as game_1_away_score,
        
        -- Parse game 2
        case 
            when len(string_split(rubber_score, ' ')) >= 2 
            then string_split(string_split(rubber_score, ' ')[2], '-')[1]::int 
        end as game_2_home_score,
        case 
            when len(string_split(rubber_score, ' ')) >= 2 
            then string_split(string_split(rubber_score, ' ')[2], '-')[2]::int 
        end as game_2_away_score,
        
        -- Parse game 3 (if exists)
        case 
            when len(string_split(rubber_score, ' ')) >= 3 
            then string_split(string_split(rubber_score, ' ')[3], '-')[1]::int 
        end as game_3_home_score,
        case 
            when len(string_split(rubber_score, ' ')) >= 3 
            then string_split(string_split(rubber_score, ' ')[3], '-')[2]::int 
        end as game_3_away_score
        
    from rubbers_unpivoted
),

games_with_winners as (
    -- Determine winners for each game and rubber
    select
        *,
        
        -- Game 1 winner
        case 
            when game_1_home_score > game_1_away_score then 'home'
            when game_1_home_score < game_1_away_score then 'away'
            else 'tie'
        end as game_1_winner,
        
        -- Game 2 winner
        case 
            when game_2_home_score > game_2_away_score then 'home'
            when game_2_home_score < game_2_away_score then 'away'
            when game_2_home_score is null then null
            else 'tie'
        end as game_2_winner,
        
        -- Game 3 winner
        case 
            when game_3_home_score > game_3_away_score then 'home'
            when game_3_home_score < game_3_away_score then 'away'
            when game_3_home_score is null then null
            else 'tie'
        end as game_3_winner,
        
        -- Rubber winner (best of 2 or 3)
        case
            -- If 2 games played
            when total_games_in_rubber = 2 then
                case
                    when (case when game_1_home_score > game_1_away_score then 1 else 0 end +
                          case when game_2_home_score > game_2_away_score then 1 else 0 end) >= 2 then 'home'
                    else 'away'
                end
            -- If 3 games played
            when total_games_in_rubber = 3 then
                case
                    when (case when game_1_home_score > game_1_away_score then 1 else 0 end +
                          case when game_2_home_score > game_2_away_score then 1 else 0 end +
                          case when game_3_home_score > game_3_away_score then 1 else 0 end) >= 2 then 'home'
                    else 'away'
                end
        end as rubber_winner,
        
        -- Home team games won
        (case when game_1_home_score > game_1_away_score then 1 else 0 end +
         case when game_2_home_score > game_2_away_score then 1 else 0 end +
         case when game_3_home_score > game_3_away_score then 1 else 0 end) as home_games_won,
        
        -- Away team games won
        (case when game_1_home_score < game_1_away_score then 1 else 0 end +
         case when game_2_home_score < game_2_away_score then 1 else 0 end +
         case when game_3_home_score < game_3_away_score then 1 else 0 end) as away_games_won
        
    from games_parsed
),

final as (
    select
        match_id,
        home_team,
        away_team,
        match_date,
        division,
        venue,
        rubber_number,
        home_player_1,
        home_player_2,
        away_player_1,
        away_player_2,
        rubber_score,
        total_games_in_rubber,
        
        -- Game 1 details
        game_1_home_score,
        game_1_away_score,
        game_1_winner,
        
        -- Game 2 details
        game_2_home_score,
        game_2_away_score,
        game_2_winner,
        
        -- Game 3 details
        game_3_home_score,
        game_3_away_score,
        game_3_winner,
        
        -- Rubber summary
        home_games_won,
        away_games_won,
        rubber_winner,
        
        -- Helpful flags
        case when total_games_in_rubber = 3 then true else false end as went_to_three_games,
        case when rubber_winner = 'home' then home_team else away_team end as rubber_winner_team,
        case when rubber_winner = 'home' then away_team else home_team end as rubber_loser_team,
        
        -- Margin of victory for each game
        abs(game_1_home_score - game_1_away_score) as game_1_margin,
        abs(game_2_home_score - game_2_away_score) as game_2_margin,
        case 
            when game_3_home_score is not null 
            then abs(game_3_home_score - game_3_away_score)
            else null
        end as game_3_margin,
        
        -- Went to deuce/extended play (winner scored > 21)
        case 
            when game_1_home_score > 21 or game_1_away_score > 21 then true 
            else false 
        end as game_1_went_to_deuce,
        case 
            when game_2_home_score > 21 or game_2_away_score > 21 then true 
            else false 
        end as game_2_went_to_deuce,
        case 
            when game_3_home_score is not null and (game_3_home_score > 21 or game_3_away_score > 21) then true
            when game_3_home_score is null then null
            else false 
        end as game_3_went_to_deuce,
        
        -- Forfeit flag (one side didn't show up)
        case 
            when (home_player_1 is null and home_player_2 is null) 
                or (away_player_1 is null and away_player_2 is null)
            then true
            else false
        end as is_forfeit
        
    from games_with_winners
)

select * from final
