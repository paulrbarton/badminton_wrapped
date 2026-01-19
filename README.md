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

## Project Structure

```
badminton-wrapped/
├── scraping/
│   ├── config.py              # Configuration (URLs, paths, settings)
│   ├── scraper.py             # BadmintonScraper class with Selenium
│   ├── parsers.py             # HTML parsing functions
│   ├── main.py                # Main orchestration script
│   └── test_single_match.py   # Testing utility
├── dbt_project/
│   ├── models/
│   │   └── staging/
│   │       ├── stg_divisions.sql  # Division/draw data
│   │       ├── stg_matches.sql    # Match-level data
│   │       ├── stg_games.sql      # Game-level details
│   │       └── schema.yml         # Model documentation
│   ├── profiles.yml           # DuckDB connection config
│   └── dbt_project.yml        # dbt project config
├── data/
│   ├── raw/                   # CSV files (divisions, matches, games)
│   └── badminton_wrapped.duckdb  # DuckDB database
└── .venv/                     # Python 3.14 for scraping
└── .venv_dbt/                 # Python 3.12 for dbt
```

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

# Run staging models
dbt run --profiles-dir .

# Test data quality
dbt test --profiles-dir .
```

**Staging Models**:
- `stg_divisions` - Division/draw information
- `stg_matches` - Match-level data (date, teams, score, venue)
- `stg_games` - Game-level details with player names and rubber scores (R1, R2, R3...)

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

### games.csv Format

Each row represents one complete match with all games (rubbers) as columns:

- **Match Info**: `match_id`, `home_team`, `away_team`, `date`, `time`, `division`, `venue`, `score`
- **Game Details**: Sequential rubbers numbered R1, R2, R3... (regardless of game type)
  - `R1_Home_P1` - Home player 1 name
  - `R1_Home_P2` - Home player 2 name
  - `R1_Away_P1` - Away player 1 name
  - `R1_Away_P2` - Away player 2 name
  - `R1_Score` - Set-by-set score (e.g., "21-19, 18-21, 21-15")

**Note**: Changed from game-type-specific columns (MD1, WD1, XD1) to unified rubber numbering (R1, R2, R3...) for easier analysis.

## Technical Notes

- **Python Versions**: 3.14 for scraping, 3.12 for dbt (due to pydantic v1 compatibility requirements)
- **Browser**: Chrome 144+ with ChromeDriver 143+
- **Database**: DuckDB (lightweight, embedded, SQL analytics)
- **Data Format**: Flat CSV structure (one row per match) for simplicity
- **Paths**: All dbt models use absolute paths to avoid portability issues

## Next Steps

- [ ] Create dbt mart models for analytics
- [ ] Player-level aggregations
- [ ] Team performance metrics
- [ ] Visualization scripts
- [ ] Wrapped-style summary reports
