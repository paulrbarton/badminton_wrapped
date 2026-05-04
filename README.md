# Badminton Wrapped

A data pipeline for scraping, transforming, and visualizing badminton match data from the Nottinghamshire Badminton League. Supports multiple seasons.

## Project Overview

This project extracts detailed match and game data from Tournament Software, loads it into DuckDB via dbt, and prepares it for analysis and visualization.

**Data Sources**:
- [2024-25 Season](https://be.tournamentsoftware.com/sport/events.aspx?id=73AE9D42-2FDF-48B1-B9CE-CA35B0B18517)
- [2025-26 Season](https://be.tournamentsoftware.com/sport/events.aspx?id=ACB2DE1B-113D-450F-A961-EA543B10373E&tlt=1)

**Supported Seasons**:
| Season | Tournament ID | Status |
|--------|--------------|--------|
| 2024-25 | `73AE9D42-2FDF-48B1-B9CE-CA35B0B18517` | ✅ Complete |
| 2025-26 | `ACB2DE1B-113D-450F-A961-EA543B10373E` | 🚧 In progress |

**Current Status**:
- ✅ Multi-season scraping support
- ✅ dbt staging models with `season` column
- ✅ Intermediate models for player-level rubber analysis
- ✅ Mart models for 10 club award types
- ✅ Award image generation with partnership and season support

## Setup

### 1. Scraping Environment (Python 3.14)

```bash
# Create virtual environment for scraping
python3.14 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install selenium beautifulsoup4 lxml

# Install ChromeDriver (macOS)
brew install chromedriver
xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver
```

### 2. dbt Environment (Python 3.12)

```bash
# Create separate virtual environment for dbt
python3.12 -m venv .venv_dbt
source .venv_dbt/bin/activate

# Install dbt with DuckDB adapter
pip install dbt-core dbt-duckdb
```

## Usage

### Scraping Data

```bash
# Activate scraping environment
source .venv/bin/activate

# Run full scraper for default season (2025-26)
python3 scraping/main.py

# Run scraper for a specific season
python3 scraping/main.py --season 2024-25
python3 scraping/main.py --season 2025-26
```

**Scraper Features**:
- Multi-season support via `--season` CLI argument
- Cookie consent handling
- Rate limiting (1 second delay between requests)
- Incremental CSV saving
- Visible browser mode for debugging
- Progress logging to `scraper.log`

**Output Files** (per season in `data/raw/{season}/`):
- `data/raw/{season}/divisions.csv` - Division/draw information
- `data/raw/{season}/matches.csv` - Match-level data
- `data/raw/{season}/games.csv` - Flat format with all game details per match

### Data Transformation with dbt

```bash
# Activate dbt environment
source .venv_dbt/bin/activate
cd dbt_project

# Step 1: Load scraped CSV data into DuckDB raw tables
# (additive - each season is loaded independently without overwriting others)
python3 load_staging_tables.py --season 2024-25
python3 load_staging_tables.py --season 2025-26

# Step 2: Run dbt models (processes all loaded seasons at once)
dbt run --profiles-dir .

# Run specific model layers
dbt run --select staging --profiles-dir .
dbt run --select intermediate --profiles-dir .
dbt run --select marts --profiles-dir .

# Test data quality
dbt test --profiles-dir .

# Generate and view documentation
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
```

**Loading Pipeline**: Raw CSVs are loaded into DuckDB `raw_*` tables by `load_staging_tables.py`. Each season is loaded independently using `--season` — running for one season never overwrites another. dbt staging models then read from these raw tables, and intermediate/mart models process all seasons together.

**Model Layers**:
- **Staging**: Views over raw DuckDB tables (all seasons)
  - `stg_divisions` - Division/draw information
  - `stg_matches` - Match-level data (date, teams, score, venue)
  - `stg_games` - Game-level details with player names and rubber scores
- **Intermediate**: Purpose-built transformations
  - `int_match_rubbers` - Rubber-level analysis with parsed game scores
  - `int_player_match_rubbers` - Player-level rubber participation
  - `int_player_home_divisions` - Player home division determination
  - `int_player_highest_divisions` - Player highest division played
  - `int_cross_division_matchups` - Cross-division opponent analysis
- **Marts**: Analytics-ready business entities
  - `mart_club_awards` - Club awards by player (10 award types, individual and partnership)

### Generating Award Images

```bash
# Activate dbt environment (image generator uses DuckDB)
source .venv_dbt/bin/activate

# Generate award images for a specific club (default season: 2025-26)
python3 visualization/generate_award_images.py --club "West Bridgford"

# Generate for a specific season
python3 visualization/generate_award_images.py --club "West Bridgford" --season 2024-25

# Generate for multiple clubs
python3 visualization/generate_award_images.py --club "Beeston"
```

**Award Types**:
- **Comeback King** (`most_comebacks`) - Most rubbers won after losing game 1
- **Club Stalwart** (`club_stalwart`) - Most matches played in the season
- **No Mercy** (`no_mercy`) - Largest winning margin in a 2-game rubber (partnership award)
- **Performs Under Pressure** (`performs_under_pressure`) - Most games won by exactly 2 points
- **Longest Winning Streak** (`longest_winning_streak`) - Most consecutive rubbers won
- **Defensive Wall** (`defensive_wall`) - Fewest average points conceded per rubber
- **Giant Killing** (`giant_killing`) - Defeated opponents from highest divisions above own
- **Epic Win** (`epic_win`) - Highest total points scored in a 3-game rubber win (partnership)
- **Clean Sweep Specialist** (`clean_sweep_specialist`) - Most 2-0 rubber wins (min 3)
- **Perfect Partnership** (`perfect_partnership`) - Most 2-0 wins as a pair (min 5)

**Features**:
- Shareable PNG images (1080x1920, optimized for social media)
- Gradient backgrounds with subtle racket watermark
- Partnership awards display both players on a single image
- Individual awards use format: `{player_name}_{award}.png`
- Partnership awards use format: `{player1}_and_{player2}_{award}.png`

### Querying Data

```bash
# Open DuckDB CLI
duckdb data/badminton_wrapped.duckdb

# Example queries
SELECT * FROM stg_divisions;
SELECT * FROM stg_matches WHERE home_team = 'West Bridgford 1';
SELECT match_id, R1_Home_P1, R1_Score FROM stg_games LIMIT 10;
```

## Data Schema

### Raw CSV Files

#### games.csv Format

Each row represents one complete match with all games (rubbers) as columns:

- **Match Info**: `match_id`, `home_team`, `away_team`, `date`, `time`, `division`, `venue`, `score`
- **Game Details**: Sequential rubbers numbered R1, R2, R3... (regardless of game type)
  - `R1_Home_P1` - Home player 1 name
  - `R1_Home_P2` - Home player 2 name
  - `R1_Away_P1` - Away player 1 name
  - `R1_Away_P2` - Away player 2 name
  - `R1_Score` - Set-by-set score (e.g., "21-19, 18-21, 21-15")

**Note**: Changed from game-type-specific columns (MD1, WD1, XD1) to unified rubber numbering (R1, R2, R3...) for easier analysis.

### Database Tables

#### mart_club_awards

Club awards by player with support for individual and partnership awards:

| Column | Type | Description |
|--------|------|-------------|
| `award` | varchar | Award type identifier |
| `club` | varchar | Club name |
| `season` | varchar | Season identifier (e.g., "2024-25") |
| `player` | varchar | Primary player (or first player for partnerships) |
| `player_2` | varchar | Secondary player for partnership awards (NULL for individual) |
| `award_value` | int | Award metric value |
| `award_details` | varchar | Detailed information about award achievement |

**Individual Awards** (player_2 = NULL): `most_comebacks`, `club_stalwart`, `performs_under_pressure`, `longest_winning_streak`, `defensive_wall`, `giant_killing`, `clean_sweep_specialist`

**Partnership Awards** (player_2 = partner name): `no_mercy`, `epic_win`, `perfect_partnership`

## Technical Notes

- **Python Versions**: 3.14 for scraping, 3.12 for dbt (due to pydantic v1 compatibility requirements)
- **Browser**: Chrome 144+ with ChromeDriver 143+
- **Database**: DuckDB (lightweight, embedded, SQL analytics)
- **Data Format**: Flat CSV structure (one row per match) for simplicity
- **Paths**: All dbt models use absolute paths to avoid portability issues
- **Image Generation**: PIL/Pillow for award image rendering with SF Pro font

## Key Design Patterns

### Multi-Season Support

The pipeline supports multiple seasons through:
- **Scraper**: `--season` CLI argument (default: `2025-26`)
- **Loading**: `load_staging_tables.py --season` loads CSVs into DuckDB `raw_*` tables additively (DELETE+INSERT per season)
- **dbt**: Staging views read all seasons from raw tables; intermediate/mart models process all seasons together
- **Visualization**: `--season` CLI argument filters awards by season
- **Data storage**: Season-specific CSV directories `data/raw/{season}/`; all seasons coexist in DuckDB
- **All models**: `season` column propagated from staging through marts

To add a new season, add its tournament ID to `scraping/config.py` in the `SEASONS` dict.

### Partnership Awards

The `player_2` column in `mart_club_awards` enables clean handling of partnership vs individual awards:

- **Individual awards**: `player_2 = NULL`
- **Partnership awards** (no_mercy, epic_win, perfect_partnership): `player_2 = partner_name`

This approach:
- ✅ Preserves data granularity (both players tracked in one row)
- ✅ Avoids UNION ALL duplication pattern
- ✅ Enables straightforward queries for both types
- ✅ Makes image generation conditional based on `player_2` presence
- ✅ Extensible for future pair-based awards

### Award Image File Naming

- Individual: `{player_slug}_{award}.png` (e.g., `paul_barton_most_comebacks.png`)
- Partnership: `{player1_slug}_and_{player2_slug}_{award}.png` (e.g., `mandy_lee_and_robert_tateson_no_mercy.png`)

### Awards Website

An interactive static website hosted on GitHub Pages that displays club awards across all seasons.

```bash
# Export award data from DuckDB to JSON (from scraping venv)
source .venv/bin/activate
python3 visualization/export_awards_json.py

# Preview locally
cd docs && python3 -m http.server 8000
# Open http://localhost:8000
```

**Navigation**: Season → Club → Awards

**Adding a new season to the website**:
1. Scrape and load the season data (see above)
2. Run dbt to rebuild models: `dbt run --profiles-dir . --vars '{season: "2025-26"}'`
3. Re-export: `python3 visualization/export_awards_json.py`
4. Commit and push — GitHub Pages updates automatically

**GitHub Pages Setup**: In the repository settings, set Pages source to "Deploy from a branch", branch `main`, folder `/docs`.

**Output Files** (in `docs/data/`):
- `seasons.json` — list of available seasons
- `{season}.json` — per-season file with all clubs and their awards

## Next Steps

- [ ] Player-level aggregations and statistics
- [ ] Team performance metrics
- [ ] Cross-season comparison analytics
