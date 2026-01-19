# Badminton Wrapped

A data pipeline for scraping, transforming, and visualizing badminton match data from the Nottinghamshire Badminton League 2024-25 season.

## Project Overview

This project extracts detailed match and game data from Tournament Software, loads it into DuckDB via dbt, and prepares it for analysis and visualization.

**Data Source**: [Nottinghamshire Badminton League](https://www.tournamentsoftware.com/sport/events.aspx?id=6C92CA66-DE3E-4D68-A1D7-0B8AF7ECF651)

**Current Status**:
- ✅ 20 divisions scraped
- ✅ 420 matches scraped
- ✅ Game-level details extracted with player names and scores
- ✅ dbt staging models loaded into DuckDB
- ✅ Intermediate models for player-level rubber analysis
- ✅ Mart models for club awards (Comeback King, Club Stalwart, No Mercy)
- ✅ Award image generation with partnership support

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

# Run full scraper (3 steps: divisions → matches → game details)
python3 scraping/main.py

# Test single match parser
python3 scraping/test_single_match.py
```

**Scraper Features**:
- Cookie consent handling
- Rate limiting (1 second delay between requests)
- Incremental CSV saving
- Visible browser mode for debugging
- Progress logging to `scraper.log`

**Output Files**:
- `data/raw/divisions.csv` - 20 divisions
- `data/raw/matches.csv` - 420 matches
- `data/raw/games.csv` - Flat format with all game details per match

### Data Transformation with dbt

```bash
# Activate dbt environment
source .venv_dbt/bin/activate
cd dbt_project

# Run all models (staging, intermediate, marts)
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

**Model Layers**:
- **Staging**: Light transformations from raw CSV data
  - `stg_divisions` - Division/draw information
  - `stg_matches` - Match-level data (date, teams, score, venue)
  - `stg_games` - Game-level details with player names and rubber scores
- **Intermediate**: Purpose-built transformations
  - `int_match_rubbers` - Rubber-level analysis with parsed game scores
  - `int_player_match_rubbers` - Player-level rubber participation
- **Marts**: Analytics-ready business entities
  - `mart_club_awards` - Club awards by player (supports individual and partnership awards)

### Generating Award Images

```bash
# Activate dbt environment (image generator uses DuckDB)
source .venv_dbt/bin/activate

# Generate award images for a specific club
python3 visualization/generate_award_images.py --club "West Bridgford"

# Generate for multiple clubs
python3 visualization/generate_award_images.py --club "Beeston"
```

**Award Types**:
- **Comeback King** (`most_comebacks`) - Most rubbers won after losing game 1
- **Club Stalwart** (`club_stalwart`) - Most matches played in the season
- **No Mercy** (`no_mercy`) - Largest winning margin in a 2-game rubber (partnership award)

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
| `player` | varchar | Primary player (or first player for partnerships) |
| `player_2` | varchar | Secondary player for partnership awards (NULL for individual) |
| `award_value` | int | Award metric value |
| `award_details` | varchar | Detailed information about award achievement |

**Award Types**:
- `most_comebacks` - Individual award (player_2 = NULL)
- `club_stalwart` - Individual award (player_2 = NULL)
- `no_mercy` - Partnership award (player_2 = partner name)

## Technical Notes

- **Python Versions**: 3.14 for scraping, 3.12 for dbt (due to pydantic v1 compatibility requirements)
- **Browser**: Chrome 144+ with ChromeDriver 143+
- **Database**: DuckDB (lightweight, embedded, SQL analytics)
- **Data Format**: Flat CSV structure (one row per match) for simplicity
- **Paths**: All dbt models use absolute paths to avoid portability issues
- **Image Generation**: PIL/Pillow for award image rendering with SF Pro font

## Key Design Patterns

### Partnership Awards

The `player_2` column in `mart_club_awards` enables clean handling of partnership vs individual awards:

- **Individual awards** (most_comebacks, club_stalwart): `player_2 = NULL`
- **Partnership awards** (no_mercy): `player_2 = partner_name`

This approach:
- ✅ Preserves data granularity (both players tracked in one row)
- ✅ Avoids UNION ALL duplication pattern
- ✅ Enables straightforward queries for both types
- ✅ Makes image generation conditional based on `player_2` presence
- ✅ Extensible for future pair-based awards

### Award Image File Naming

- Individual: `{player_slug}_{award}.png` (e.g., `paul_barton_most_comebacks.png`)
- Partnership: `{player1_slug}_and_{player2_slug}_{award}.png` (e.g., `mandy_lee_and_robert_tateson_no_mercy.png`)

## Next Steps

- [ ] Additional award types (deuce master, clean sweep, biggest comeback)
- [ ] Player-level aggregations and statistics
- [ ] Team performance metrics
- [ ] Interactive visualization dashboard
- [ ] Automated award generation for all clubs
