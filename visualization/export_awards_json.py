#!/usr/bin/env python3
"""
Export award data from DuckDB to JSON files for the awards website.

Queries mart_club_awards for all seasons and writes:
  - docs/data/seasons.json  — list of available seasons
  - docs/data/{season}.json — per-season file with clubs and their awards
    - docs/data/inline-data.js — embedded data bundle for file:// browsing

Usage:
    python visualization/export_awards_json.py
"""

import json
import logging
import re
from pathlib import Path

import duckdb

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "badminton_wrapped.duckdb"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "data"
INLINE_DATA_PATH = OUTPUT_DIR / "inline-data.js"


def slugify(name: str) -> str:
    """Convert a club name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def _has_column(conn: duckdb.DuckDBPyConnection, table: str, column: str) -> bool:
    """Check if a table has a given column."""
    cols = conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = ?",
        [table],
    ).fetchall()
    return column in {row[0] for row in cols}


def export_awards() -> None:
    """Export all award data from DuckDB to JSON files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(str(DB_PATH), read_only=True)

    has_season = _has_column(conn, "mart_club_awards", "season")

    if has_season:
        seasons = [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT season FROM mart_club_awards ORDER BY season"
            ).fetchall()
        ]
    else:
        # Infer season from match dates or fall back to directory scan
        try:
            min_date = conn.execute(
                "SELECT MIN(match_date) FROM int_player_match_rubbers"
            ).fetchone()[0]
            if min_date:
                year = int(str(min_date)[:4])
                # Badminton seasons span Sep-Apr, so a date in 2024 = 2024-25 season
                month = int(str(min_date)[5:7])
                start_year = year if month >= 8 else year - 1
                seasons = [f"{start_year}-{str(start_year + 1)[-2:]}"]
            else:
                seasons = ["2024-25"]
        except Exception:
            seasons = ["2024-25"]
        logger.info("No season column in mart_club_awards; inferred seasons: %s", seasons)

    if not seasons:
        logger.warning("No award data found in mart_club_awards")
        conn.close()
        return

    logger.info("Found seasons: %s", seasons)

    # Write seasons manifest
    seasons_path = OUTPUT_DIR / "seasons.json"
    seasons_path.write_text(json.dumps(seasons, indent=2))
    logger.info("Wrote %s", seasons_path)

    seasons_data: dict[str, dict] = {}

    # Export each season
    for season in seasons:
        if has_season:
            rows = conn.execute(
                """
                SELECT award, club, player, player_2, award_value, award_details
                FROM mart_club_awards
                WHERE season = ?
                ORDER BY club, award, player
                """,
                [season],
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT award, club, player, player_2, award_value, award_details
                FROM mart_club_awards
                ORDER BY club, award, player
                """
            ).fetchall()

        clubs: dict = {}
        slug_sources: dict[str, set[str]] = {}
        for award, club, player, player_2, award_value, award_details in rows:
            slug = slugify(club)
            slug_sources.setdefault(slug, set()).add(club)
            if slug not in clubs:
                clubs[slug] = {"name": club, "awards": []}
            clubs[slug]["awards"].append(
                {
                    "award": award,
                    "player": player,
                    "player_2": player_2,
                    "award_value": award_value,
                    "award_details": award_details,
                }
            )

        for slug, names in slug_sources.items():
            if len(names) > 1:
                logger.warning(
                    "Slug collision for season %s at slug '%s': source club names=%s",
                    season,
                    slug,
                    sorted(names),
                )

        season_data = {"season": season, "clubs": clubs}
        seasons_data[season] = season_data
        season_path = OUTPUT_DIR / f"{season}.json"
        season_path.write_text(json.dumps(season_data, indent=2))
        logger.info(
            "Wrote %s (%d clubs, %d awards)",
            season_path,
            len(clubs),
            len(rows),
        )

    inline_payload = {
        "seasons": seasons,
        "seasonsData": seasons_data,
    }
    inline_js = "window.BADMINTON_WRAPPED_DATA = " + json.dumps(inline_payload, separators=(",", ":")) + ";\n"
    INLINE_DATA_PATH.write_text(inline_js)
    logger.info("Wrote %s", INLINE_DATA_PATH)

    conn.close()
    logger.info("Export complete")


if __name__ == "__main__":
    export_awards()
