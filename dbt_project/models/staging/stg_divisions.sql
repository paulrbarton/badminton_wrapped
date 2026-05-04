-- Staging model for divisions data
-- Reads from raw_divisions table loaded by load_staging_tables.py

select
    draw_id,
    division_name,
    url,
    season,
    loaded_at
from raw_divisions
