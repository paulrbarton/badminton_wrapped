-- Staging model for game details
-- Reads from raw_games table loaded by load_staging_tables.py

select
    match_id,
    home_team,
    away_team,
    match_date,
    match_time,
    division,
    venue,
    match_score,
    R1_Home_P1, R1_Home_P2, R1_Away_P1, R1_Away_P2, R1_Score,
    R2_Home_P1, R2_Home_P2, R2_Away_P1, R2_Away_P2, R2_Score,
    R3_Home_P1, R3_Home_P2, R3_Away_P1, R3_Away_P2, R3_Score,
    R4_Home_P1, R4_Home_P2, R4_Away_P1, R4_Away_P2, R4_Score,
    R5_Home_P1, R5_Home_P2, R5_Away_P1, R5_Away_P2, R5_Score,
    R6_Home_P1, R6_Home_P2, R6_Away_P1, R6_Away_P2, R6_Score,
    R7_Home_P1, R7_Home_P2, R7_Away_P1, R7_Away_P2, R7_Score,
    R8_Home_P1, R8_Home_P2, R8_Away_P1, R8_Away_P2, R8_Score,
    R9_Home_P1, R9_Home_P2, R9_Away_P1, R9_Away_P2, R9_Score,
    season,
    loaded_at
from raw_games
