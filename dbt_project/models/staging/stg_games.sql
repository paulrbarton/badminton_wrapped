-- Staging model for game details
-- Loads detailed match data with all individual games in flat format

with source as (
    select * from read_csv_auto('/Users/c16305a/Documents/ECS/Sandpit/badminton-wrapped/data/raw/{{ var("season") }}/games.csv', header=true)
),

renamed as (
    select
        match_id,
        home_team,
        away_team,
        date as match_date,
        time as match_time,
        division,
        venue,
        score as match_score,
        
        -- Rubbers (9 per match in badminton)
        R1_Home_P1, R1_Home_P2, R1_Away_P1, R1_Away_P2, R1_Score,
        R2_Home_P1, R2_Home_P2, R2_Away_P1, R2_Away_P2, R2_Score,
        R3_Home_P1, R3_Home_P2, R3_Away_P1, R3_Away_P2, R3_Score,
        R4_Home_P1, R4_Home_P2, R4_Away_P1, R4_Away_P2, R4_Score,
        R5_Home_P1, R5_Home_P2, R5_Away_P1, R5_Away_P2, R5_Score,
        R6_Home_P1, R6_Home_P2, R6_Away_P1, R6_Away_P2, R6_Score,
        R7_Home_P1, R7_Home_P2, R7_Away_P1, R7_Away_P2, R7_Score,
        R8_Home_P1, R8_Home_P2, R8_Away_P1, R8_Away_P2, R8_Score,
        R9_Home_P1, R9_Home_P2, R9_Away_P1, R9_Away_P2, R9_Score,
        
        '{{ var("season") }}' as season,
        current_timestamp as loaded_at
    from source
)

select * from renamed
