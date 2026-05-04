-- Staging model for matches data
-- Reads from raw_matches table loaded by load_staging_tables.py

select
    match_id,
    draw_id,
    division_name,
    match_date,
    home_team,
    away_team,
    score,
    url,
    season,
    loaded_at
from raw_matches
