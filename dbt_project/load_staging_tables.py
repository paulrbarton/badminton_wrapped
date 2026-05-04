"""
Direct DuckDB script to load CSV files into staging tables.
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

# Create staging tables
print("\n1. Creating staging tables...")

# stg_divisions
print("   - Creating stg_divisions...")
conn.execute(f"""
    CREATE OR REPLACE TABLE stg_divisions AS
    SELECT 
        draw_id,
        division_name,
        url,
        '{season}' as season,
        current_timestamp as loaded_at
    FROM read_csv_auto('{raw_dir}/divisions.csv', header=true)
""")

# stg_matches  
print("   - Creating stg_matches...")
conn.execute(f"""
    CREATE OR REPLACE TABLE stg_matches AS
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

# stg_games (flat format with all game columns)
print("   - Creating stg_games...")
conn.execute(f"""
    CREATE OR REPLACE TABLE stg_games AS
    SELECT 
        match_id,
        home_team,
        away_team,
        date as match_date,
        time as match_time,
        division,
        venue,
        score as match_score,
        
        -- Men's Doubles games
        MD1_Home_P1, MD1_Home_P2, MD1_Away_P1, MD1_Away_P2, MD1_Score,
        MD2_Home_P1, MD2_Home_P2, MD2_Away_P1, MD2_Away_P2, MD2_Score,
        MD3_Home_P1, MD3_Home_P2, MD3_Away_P1, MD3_Away_P2, MD3_Score,
        MD4_Home_P1, MD4_Home_P2, MD4_Away_P1, MD4_Away_P2, MD4_Score,
        MD5_Home_P1, MD5_Home_P2, MD5_Away_P1, MD5_Away_P2, MD5_Score,
        MD6_Home_P1, MD6_Home_P2, MD6_Away_P1, MD6_Away_P2, MD6_Score,
        MD7_Home_P1, MD7_Home_P2, MD7_Away_P1, MD7_Away_P2, MD7_Score,
        MD8_Home_P1, MD8_Home_P2, MD8_Away_P1, MD8_Away_P2, MD8_Score,
        MD9_Home_P1, MD9_Home_P2, MD9_Away_P1, MD9_Away_P2, MD9_Score,
        
        -- Women's Doubles games
        WD1_Home_P1, WD1_Home_P2, WD1_Away_P1, WD1_Away_P2, WD1_Score,
        WD2_Home_P1, WD2_Home_P2, WD2_Away_P1, WD2_Away_P2, WD2_Score,
        WD3_Home_P1, WD3_Home_P2, WD3_Away_P1, WD3_Away_P2, WD3_Score,
        
        -- Mixed Doubles games
        XD1_Home_P1, XD1_Home_P2, XD1_Away_P1, XD1_Away_P2, XD1_Score,
        XD2_Home_P1, XD2_Home_P2, XD2_Away_P1, XD2_Away_P2, XD2_Score,
        XD3_Home_P1, XD3_Home_P2, XD3_Away_P1, XD3_Away_P2, XD3_Score,
        
        '{season}' as season,
        current_timestamp as loaded_at
    FROM read_csv_auto('{raw_dir}/games.csv', header=true)
""")

print("\n2. Verifying tables...")

# Get row counts
divisions_count = conn.execute("SELECT COUNT(*) FROM stg_divisions").fetchone()[0]
matches_count = conn.execute("SELECT COUNT(*) FROM stg_matches").fetchone()[0]
games_count = conn.execute("SELECT COUNT(*) FROM stg_games").fetchone()[0]

print(f"   - stg_divisions: {divisions_count} rows")
print(f"   - stg_matches: {matches_count} rows")
print(f"   - stg_games: {games_count} rows")

print("\n3. Sample data from each table:")

print("\n   stg_divisions (first 3 rows):")
print(conn.execute("SELECT * FROM stg_divisions LIMIT 3").df().to_string(index=False))

print("\n   stg_matches (first 3 rows):")
print(conn.execute("SELECT match_id, division_name, home_team, away_team, score FROM stg_matches LIMIT 3").df().to_string(index=False))

print("\n   stg_games (first row, basic columns):")
print(conn.execute("SELECT match_id, home_team, away_team, match_date, venue, match_score FROM stg_games LIMIT 1").df().to_string(index=False))

print("\n" + "="*60)
print("✓ All staging tables created successfully in DuckDB!")
print(f"✓ Database location: {db_path}")
print("="*60)

conn.close()
