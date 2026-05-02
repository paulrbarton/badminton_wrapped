"""
Configuration settings for the badminton league scraper.
"""
from pathlib import Path

# Base URL for Tournament Software
BASE_URL = "https://be.tournamentsoftware.com"

# Season configurations
SEASONS = {
    "2024-25": {
        "tournament_id": "73AE9D42-2FDF-48B1-B9CE-CA35B0B18517",
        "season_name": "Nottinghamshire 2024-25",
        "events_url_extra_params": "",
    },
    "2025-26": {
        "tournament_id": "ACB2DE1B-113D-450F-A961-EA543B10373E",
        "season_name": "Nottingham 2025-26",
        "events_url_extra_params": "&tlt=1",
    },
}

# Default season to scrape
DEFAULT_SEASON = "2025-26"

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def get_season_config(season: str) -> dict:
    """
    Get configuration for a specific season.

    Args:
        season: Season key (e.g., "2024-25", "2025-26")

    Returns:
        Dictionary with resolved URLs and paths for the season
    """
    if season not in SEASONS:
        raise ValueError(f"Unknown season '{season}'. Available: {list(SEASONS.keys())}")

    cfg = SEASONS[season]
    tid = cfg["tournament_id"]

    data_raw_dir = PROJECT_ROOT / "data" / "raw" / season
    data_raw_dir.mkdir(parents=True, exist_ok=True)

    return {
        "season": season,
        "season_name": cfg["season_name"],
        "tournament_id": tid,
        "data_raw_dir": data_raw_dir,
        "divisions_csv": data_raw_dir / "divisions.csv",
        "matches_csv": data_raw_dir / "matches.csv",
        "games_csv": data_raw_dir / "games.csv",
        "events_url": f"{BASE_URL}/sport/events.aspx?id={tid}{cfg['events_url_extra_params']}",
        "drawmatches_url": f"{BASE_URL}/sport/drawmatches.aspx?id={tid}&draw={{draw_id}}",
        "teammatch_url": f"{BASE_URL}/sport/teammatch.aspx?id={tid}&match={{match_id}}",
    }


# Scraping settings
REQUEST_DELAY = 1  # seconds between requests to be respectful
PAGE_LOAD_TIMEOUT = 10  # seconds to wait for page elements
IMPLICIT_WAIT = 5  # seconds for Selenium implicit wait

# Selenium settings
HEADLESS = False  # Run browser in headless mode (set to False to see what's happening)
WINDOW_SIZE = (1920, 1080)  # Browser window size

# User agent (optional - use realistic one)
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Cookie consent selectors to try (in order)
COOKIE_CONSENT_SELECTORS = [
    "//button[contains(@class, 'js-accept-basic')]",  # From actual HTML
    "//button[contains(text(), 'Accept')]",
    "//button[contains(text(), 'ACCEPT')]",
    "button.js-accept-basic",
    "button.btn--success",
    "//a[contains(text(), 'ACCEPT')]",
    "//button[@id='accept-cookies']",
    ".cookie-accept",
    "#cookie-accept"
]
