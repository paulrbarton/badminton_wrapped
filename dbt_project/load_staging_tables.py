"""
Direct DuckDB script to load CSV files into raw staging tables.
Uses DELETE+INSERT pattern to support additive multi-season loading.
Workaround for Python 3.14 compatibility issues with dbt.
"""
import argparse
import duckdb
from pathlib import Path

# Parse arguments
parser = argparse.ArgumentParser(description='Load staging tables for a specific season')
parser.add_argument('--season', default='2025-26', help='Season to load (default: 2025-26)')
args = parser.parse_args()
season = args.season

# Connect to DuckDB
db_path = Path(__file__).parent.parent / 'data' / 'badminton_wrapped.duckdb'
conn = duckdb.connect(str(db_path))

raw_dir = Path(__file__).parent.parent / 'data' / 'raw' / season

print(f"Connected to DuckDB at: {db_path}")
print(f"Loading season: {season}")
print(f"Raw data directory: {raw_dir}")
print("="*60)

# Create raw tables (if they don't exist) and load data
print("\n1. Loading raw tables...")

# raw_divisions
print("   - Loading raw_divisions...")
conn.execute("""
    CREATE TABLE IF NOT EXISTS raw_divisions (
        draw_id VARCHAR,
        division_name VARCHAR,
        url VARCHAR,
        season VARCHAR,
        loaded_at TIMESTAMP
    )
""")
conn.execute(f"DELETE FROM raw_divisions WHERE season = '{season}'")
conn.execute(f"""
    INSERT INTO raw_divisions
    SELECT 
        draw_id,
        division_name,
        url,
        '{season}' as season,
        current_timestamp as loaded_at
    FROM read_csv_auto('{raw_dir}/divisions.csv', header=true)
""")

# raw_matches
print("   - Loading raw_matches...")
conn.execute("""
    CREATE TABLE IF NOT EXISTS raw_matches (
        match_id VARCHAR,
        draw_id VARCHAR,
        division_name VARCHAR,
        match_date VARCHAR,
        home_team VARCHAR,
        away_team VARCHAR,
        score VARCHAR,
        url VARCHAR,
        season VARCHAR,
        loaded_at TIMESTAMP
    )
""")
conn.execute(f"DELETE FROM raw_matches WHERE season = '{season}'")
conn.execute(f"""
    INSERT INTO raw_matches
    SELECT 
        match_id,
        draw_id,
        division_name,
        match_date,
        home_team,
        away_team,
        score,
        url,
        '{season}' as season,
        current_timestamp as loaded_at
    FROM read_csv_auto('{raw_dir}/matches.csv', header=true)
""")

# raw_games (flat format with R1-R9 rubber columns)
print("   - Loading raw_games...")
conn.execute("""
    CREATE TABLE IF NOT EXISTS raw_games (
        match_id VARCHAR,
        home_team VARCHAR,
        away_team VARCHAR,
        match_date VARCHAR,
        match_time VARCHAR,
        division VARCHAR,
        venue VARCHAR,
        match_score VARCHAR,
        R1_Home_P1 VARCHAR, R1_Home_P2 VARCHAR, R1_Away_P1 VARCHAR, R1_Away_P2 VARCHAR, R1_Score VARCHAR,
        R2_Home_P1 VARCHAR, R2_Home_P2 VARCHAR, R2_Away_P1 VARCHAR, R2_Away_P2 VARCHAR, R2_Score VARCHAR,
        R3_Home_P1 VARCHAR, R3_Home_P2 VARCHAR, R3_Away_P1 VARCHAR, R3_Away_P2 VARCHAR, R3_Score VARCHAR,
        R4_Home_P1 VARCHAR, R4_Home_P2 VARCHAR, R4_Away_P1 VARCHAR, R4_Away_P2 VARCHAR, R4_Score VARCHAR,
        R5_Home_P1 VARCHAR, R5_Home_P2 VARCHAR, R5_Away_P1 VARCHAR, R5_Away_P2 VARCHAR, R5_Score VARCHAR,
        R6_Home_P1 VARCHAR, R6_Home_P2 VARCHAR, R6_Away_P1 VARCHAR, R6_Away_P2 VARCHAR, R6_Score VARCHAR,
        R7_Home_P1 VARCHAR, R7_Home_P2 VARCHAR, R7_Away_P1 VARCHAR, R7_Away_P2 VARCHAR, R7_Score VARCHAR,
        R8_Home_P1 VARCHAR, R8_Home_P2 VARCHAR, R8_Away_P1 VARCHAR, R8_Away_P2 VARCHAR, R8_Score VARCHAR,
        R9_Home_P1 VARCHAR, R9_Home_P2 VARCHAR, R9_Away_P1 VARCHAR, R9_Away_P2 VARCHAR, R9_Score VARCHAR,
        season VARCHAR,
        loaded_at TIMESTAMP
    )
""")
conn.execute(f"DELETE FROM raw_games WHERE season = '{season}'")
conn.execute(f"""
    INSERT INTO raw_games
    SELECT 
        match_id,
        home_team,
        away_team,
        date as match_date,
        time as match_time,
        division,
        venue,
        score as match_score,
        R1_Home_P1, R1_Home_P2, R1_Away_P1, R1_Away_P2, R1_Score,
        R2_Home_P1, R2_Home_P2, R2_Away_P1, R2_Away_P2, R2_Score,
        R3_Home_P1, R3_Home_P2, R3_Away_P1, R3_Away_P2, R3_Score,
        R4_Home_P1, R4_Home_P2, R4_Away_P1, R4_Away_P2, R4_Score,
        R5_Home_P1, R5_Home_P2, R5_Away_P1, R5_Away_P2, R5_Score,
        R6_Home_P1, R6_Home_P2, R6_Away_P1, R6_Away_P2, R6_Score,
        R7_Home_P1, R7_Home_P2, R7_Away_P1, R7_Away_P2, R7_Score,
        R8_Home_P1, R8_Home_P2, R8_Away_P1, R8_Away_P2, R8_Score,
        R9_Home_P1, R9_Home_P2, R9_Away_P1, R9_Away_P2, R9_Score,
        '{season}' as season,
        current_timestamp as loaded_at
    FROM read_csv_auto('{raw_dir}/games.csv', header=true)
""")

print("\n2. Verifying tables...")

# Get row counts per season
for table in ['raw_divisions', 'raw_matches', 'raw_games']:
    total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    seasons = conn.execute(f"SELECT season, COUNT(*) as cnt FROM {table} GROUP BY season ORDER BY season").fetchall()
    season_str = ', '.join([f"{s}: {c}" for s, c in seasons])
    print(f"   - {table}: {total} total rows ({season_str})")

print("\n3. Sample data from each table:")

print(f"\n   raw_divisions (season={season}, first 3 rows):")
print(conn.execute(f"SELECT * FROM raw_divisions WHERE season = '{season}' LIMIT 3").df().to_string(index=False))

print(f"\n   raw_matches (season={season}, first 3 rows):")
print(conn.execute(f"SELECT match_id, division_name, home_team, away_team, score, season FROM raw_matches WHERE season = '{season}' LIMIT 3").df().to_string(index=False))

print(f"\n   raw_games (season={season}, first row, basic columns):")
print(conn.execute(f"SELECT match_id, home_team, away_team, match_date, venue, match_score, season FROM raw_games WHERE season = '{season}' LIMIT 1").df().to_string(index=False))

print("\n" + "="*60)
print(f"✓ Season {season} loaded successfully into raw tables!")
print(f"✓ Database location: {db_path}")
print("="*60)

conn.close()
