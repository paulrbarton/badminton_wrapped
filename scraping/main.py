"""
Main script to orchestrate the scraping of Nottinghamshire Badminton League data.
"""
import logging
import pandas as pd
from typing import List, Dict
import sys

from config import (
    EVENTS_URL,
    DRAWMATCHES_URL,
    TEAMMATCH_URL,
    DIVISIONS_CSV,
    MATCHES_CSV,
    GAMES_CSV
)
from scraper import BadmintonScraper
from parsers import parse_divisions, parse_matches, parse_match_details

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def scrape_all_data():
    """Main function to scrape all badminton league data."""
    logger.info("="*60)
    logger.info("Starting Nottinghamshire Badminton League scraper")
    logger.info("="*60)
    
    all_divisions = []
    all_matches = []
    all_match_details = []
    
    try:
        with BadmintonScraper() as scraper:
            # Step 1: Scrape divisions
            logger.info("\n--- STEP 1: Scraping divisions ---")
            if not scraper.get_page(EVENTS_URL):
                logger.error("Failed to load events page")
                return
            
            html = scraper.get_page_source()
            
            # Debug: save the HTML to inspect it
            debug_file = "debug_events_page.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"Saved page HTML to {debug_file} for debugging")
            
            divisions = parse_divisions(html)
            
            if not divisions:
                logger.error("No divisions found!")
                return
            
            logger.info(f"Found {len(divisions)} divisions")
            all_divisions.extend(divisions)
            
            # Save divisions immediately
            if all_divisions:
                df_divisions = pd.DataFrame(all_divisions)
                df_divisions.to_csv(DIVISIONS_CSV, index=False)
                logger.info(f"Saved {len(all_divisions)} divisions to {DIVISIONS_CSV}")
            
            # Step 2: Scrape matches for each division
            logger.info("\n--- STEP 2: Scraping matches from each division ---")
            logger.info(f"Total divisions to process: {len(divisions)}")
            
            for i, division in enumerate(divisions, 1):
                logger.info(f"\n[{i}/{len(divisions)}] Processing division: {division['division_name']}")
                
                url = DRAWMATCHES_URL.format(draw_id=division['draw_id'])
                if not scraper.get_page(url):
                    logger.warning(f"Failed to load matches for {division['division_name']}")
                    continue
                
                html = scraper.get_page_source()
                matches = parse_matches(
                    html,
                    division['division_name'],
                    division['draw_id']
                )
                
                logger.info(f"Found {len(matches)} matches in {division['division_name']}")
                all_matches.extend(matches)
                
                # Save matches incrementally after each division
                if all_matches:
                    df_matches = pd.DataFrame(all_matches)
                    df_matches.to_csv(MATCHES_CSV, index=False)
                    logger.debug(f"Incremental save: {len(all_matches)} total matches")
            
            # Save final matches data
            if all_matches:
                df_matches = pd.DataFrame(all_matches)
                df_matches.to_csv(MATCHES_CSV, index=False)
                logger.info(f"Saved {len(all_matches)} matches to {MATCHES_CSV}")
            
            # Step 3: Scrape details for each match (flat format)
            logger.info("\n--- STEP 3: Scraping match details (flat format) ---")
            total_matches = len(all_matches)
            logger.info(f"Total matches to process: {total_matches}")
            
            if total_matches > 50:
                logger.warning(f"Processing {total_matches} matches will take approximately {total_matches * 1.5 / 60:.1f} minutes")
            
            all_match_details = []
            
            for i, match in enumerate(all_matches, 1):
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{total_matches} matches processed ({i*100//total_matches}%)")
                    # Save progress every 10 matches
                    if all_match_details:
                        df_details = pd.DataFrame(all_match_details)
                        df_details.to_csv(GAMES_CSV, index=False)
                        logger.debug(f"Incremental save: {len(all_match_details)} matches with full details")
                
                logger.debug(f"Processing match {i}/{total_matches}: Match ID {match['match_id']}")
                
                url = TEAMMATCH_URL.format(match_id=match['match_id'])
                if not scraper.get_page(url):
                    logger.warning(f"Failed to load details for match {match['match_id']}")
                    continue
                
                html = scraper.get_page_source()
                match_details = parse_match_details(
                    html=html,
                    match_id=match['match_id'],
                    home_team=match.get('home_team'),
                    away_team=match.get('away_team'),
                    date=match.get('match_date'),
                    division=match['division_name']
                )
                
                all_match_details.append(match_details)
        
        # Step 4: Save data to CSV files
        logger.info("\n--- STEP 4: Saving data to CSV files ---")
        
        # Save divisions
        if all_divisions:
            df_divisions = pd.DataFrame(all_divisions)
            df_divisions.to_csv(DIVISIONS_CSV, index=False)
            logger.info(f"Saved {len(all_divisions)} divisions to {DIVISIONS_CSV}")
        
        # Save matches
        if all_matches:
            df_matches = pd.DataFrame(all_matches)
            df_matches.to_csv(MATCHES_CSV, index=False)
            logger.info(f"Saved {len(all_matches)} matches to {MATCHES_CSV}")
        
        # Save match details (flat format with all games)
        if all_match_details:
            df_details = pd.DataFrame(all_match_details)
            df_details.to_csv(GAMES_CSV, index=False)
            logger.info(f"Saved {len(all_match_details)} matches with full game details to {GAMES_CSV}")
            logger.info(f"Total columns: {len(df_details.columns)}")
        
        logger.info("\n" + "="*60)
        logger.info("Scraping completed successfully!")
        logger.info(f"Summary:")
        logger.info(f"  - Divisions: {len(all_divisions)}")
        logger.info(f"  - Matches: {len(all_matches)}")
        logger.info(f"  - Match details: {len(all_match_details)} (flat format)")
        logger.info("="*60)
        
    except KeyboardInterrupt:
        logger.info("\n\nScraping interrupted by user")
        # Still try to save partial data
        if all_divisions:
            pd.DataFrame(all_divisions).to_csv(DIVISIONS_CSV, index=False)
        if all_matches:
            pd.DataFrame(all_matches).to_csv(MATCHES_CSV, index=False)
        if all_match_details:
            pd.DataFrame(all_match_details).to_csv(GAMES_CSV, index=False)
        logger.info("Partial data saved")
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    scrape_all_data()
