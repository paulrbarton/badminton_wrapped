"""
Configuration settings for the badminton league scraper.
"""
from pathlib import Path

# Base URL for Tournament Software
BASE_URL = "https://be.tournamentsoftware.com"

# Tournament ID for Nottinghamshire League 2024-25
TOURNAMENT_ID = "73AE9D42-2FDF-48B1-B9CE-CA35B0B18517"

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Output file paths
DIVISIONS_CSV = DATA_RAW_DIR / "divisions.csv"
MATCHES_CSV = DATA_RAW_DIR / "matches.csv"
GAMES_CSV = DATA_RAW_DIR / "games.csv"

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

# Page URLs
EVENTS_URL = f"{BASE_URL}/sport/events.aspx?id={TOURNAMENT_ID}"
DRAWMATCHES_URL = f"{BASE_URL}/sport/drawmatches.aspx?id={TOURNAMENT_ID}&draw={{draw_id}}"
TEAMMATCH_URL = f"{BASE_URL}/sport/teammatch.aspx?id={TOURNAMENT_ID}&match={{match_id}}"
