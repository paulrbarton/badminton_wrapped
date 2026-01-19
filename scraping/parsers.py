"""
HTML parsing functions for extracting badminton match data.
"""
import re
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_divisions(html: str) -> List[Dict[str, any]]:
    """
    Parse the divisions/events page to extract division names and IDs.
    
    Args:
        html: HTML source of the events page
        
    Returns:
        List of dictionaries containing division information
    """
    soup = BeautifulSoup(html, 'html.parser')
    divisions = []
    
    # Find the main table with divisions
    table = soup.find('table', class_='ruler')
    if not table:
        logger.error("Could not find divisions table with class 'ruler'")
        return divisions
    
    tbody = table.find('tbody')
    if not tbody:
        logger.error("Could not find tbody in divisions table")
        return divisions
    
    rows = tbody.find_all('tr')
    logger.info(f"Found {len(rows)} division rows")
    
    for row in rows:
        try:
            # Find link to draw page (could be draw.aspx or drawmatches.aspx)
            link = row.find('a', href=re.compile(r'draw.*\.aspx.*draw='))
            if not link:
                continue
            
            href = link.get('href')
            division_name = link.get_text(strip=True)
            
            # Extract draw ID from URL
            match = re.search(r'draw=(\d+)', href)
            if match:
                draw_id = int(match.group(1))
                
                divisions.append({
                    'draw_id': draw_id,
                    'division_name': division_name,
                    'url': href
                })
                logger.info(f"Parsed division: {division_name} (draw_id: {draw_id})")
        
        except Exception as e:
            logger.error(f"Error parsing division row: {str(e)}")
            continue
    
    return divisions


def parse_matches(html: str, division_name: str, draw_id: int) -> List[Dict[str, any]]:
    """
    Parse the matches page for a specific division to extract match details.
    
    Args:
        html: HTML source of the drawmatches page
        division_name: Name of the division
        draw_id: Division ID
        
    Returns:
        List of dictionaries containing match information
    """
    soup = BeautifulSoup(html, 'html.parser')
    matches = []
    
    # Find the matches table
    table = soup.find('table', class_='matches')
    if not table:
        logger.error(f"Could not find matches table for division {division_name}")
        return matches
    
    tbody = table.find('tbody')
    if not tbody:
        logger.error(f"Could not find tbody in matches table for {division_name}")
        return matches
    
    rows = tbody.find_all('tr')
    logger.info(f"Found {len(rows)} match rows in {division_name}")
    
    for row in rows:
        try:
            cells = row.find_all('td')
            if len(cells) < 4:
                continue
            
            # Find link to match details
            match_link = row.find('a', href=re.compile(r'teammatch\.aspx'))
            if not match_link:
                continue
            
            href = match_link.get('href')
            
            # Extract match ID from URL
            match_id_search = re.search(r'match=(\d+)', href)
            if not match_id_search:
                continue
            
            match_id = int(match_id_search.group(1))
            
            # Extract match data from cells
            # The structure may vary, so we'll be flexible
            match_date = cells[0].get_text(strip=True) if len(cells) > 0 else None
            
            # Try to find team names - they're often in links
            team_links = row.find_all('a', href=re.compile(r'team\.aspx'))
            if len(team_links) >= 2:
                home_team = team_links[0].get_text(strip=True)
                away_team = team_links[1].get_text(strip=True)
            else:
                # Fallback: try to extract from text
                text_parts = [cell.get_text(strip=True) for cell in cells]
                home_team = text_parts[1] if len(text_parts) > 1 else None
                away_team = text_parts[3] if len(text_parts) > 3 else None
            
            # Extract score (usually in the middle cell)
            score_cell = None
            for cell in cells:
                cell_text = cell.get_text(strip=True)
                if '-' in cell_text and re.match(r'\d+\s*-\s*\d+', cell_text):
                    score_cell = cell_text
                    break
            
            matches.append({
                'match_id': match_id,
                'draw_id': draw_id,
                'division_name': division_name,
                'match_date': match_date,
                'home_team': home_team,
                'away_team': away_team,
                'score': score_cell,
                'url': href
            })
            
            logger.info(f"Parsed match {match_id}: {home_team} vs {away_team}")
        
        except Exception as e:
            logger.error(f"Error parsing match row: {str(e)}")
            continue
    
    return matches


def parse_match_details(html: str, match_id: int, home_team: str = None, away_team: str = None, 
                       date: str = None, division: str = None) -> Dict[str, any]:
    """
    Parse match HTML into a single flattened row with all games as columns.
    
    Args:
        html: HTML source of the teammatch page
        match_id: Match ID
        home_team: Home team name (optional, will extract from HTML if not provided)
        away_team: Away team name (optional, will extract from HTML if not provided)
        date: Match date (optional, will extract from HTML if not provided)
        division: Division name (optional)
        
    Returns:
        Dictionary with flat structure: all match info and games in one row
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    match_row = {
        'match_id': match_id,
        'home_team': home_team,
        'away_team': away_team,
        'date': date,
        'time': None,
        'division': division,
        'venue': None,
        'score': None
    }
    
    try:
        # Extract teams from h3 tag if not provided
        if not match_row['home_team'] or not match_row['away_team']:
            h3_tags = soup.find_all('h3')
            h3 = None
            for tag in h3_tags:
                if tag.find('a', href=lambda x: x and 'team.aspx' in x):
                    h3 = tag
                    break
            
            if h3:
                team_links = h3.find_all('a', href=lambda x: x and 'team.aspx' in x)
                if len(team_links) >= 2:
                    match_row['home_team'] = team_links[0].get_text(strip=True)
                    match_row['away_team'] = team_links[1].get_text(strip=True)
                
                # Overall score is in span.score
                score_span = h3.find('span', class_='score')
                if score_span:
                    match_row['score'] = score_span.get_text(strip=True)
        
        # Extract match details from info table
        info_table = soup.find('table')
        if info_table:
            rows = info_table.find_all('tr')
            for row in rows:
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    header = th.get_text(strip=True).lower()
                    value = td.get_text(strip=True)
                    
                    if 'time' in header:
                        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', value)
                        if date_match:
                            match_row['date'] = date_match.group(1)
                        time_match = re.search(r'(\d{2}:\d{2})', value)
                        if time_match:
                            match_row['time'] = time_match.group(1)
                    elif 'location' in header:
                        venue_link = td.find('a')
                        if venue_link:
                            match_row['venue'] = venue_link.get_text(strip=True)
        
        # Find match results table
        results_table = soup.find('table', class_='ruler matches')
        if not results_table:
            logger.warning(f"No match results table found for match {match_id}")
            return match_row
        
        tbody = results_table.find('tbody')
        if not tbody:
            logger.warning(f"No tbody in results table for match {match_id}")
            return match_row
        
        rows = tbody.find_all('tr')
        
        # Counter for rubber numbering (R1, R2, R3, etc.)
        rubber_number = 0
        
        for row in rows:
            cells = row.find_all('td', recursive=False)  # Only direct children
            if len(cells) < 5:
                continue
            
            # Cell 0: Game type (MD1, MD2, WD1, XD1, etc.) - we'll ignore the prefix
            game_type_raw = cells[0].get_text(strip=True)
            if not game_type_raw:
                continue
            
            # Increment rubber counter
            rubber_number += 1
            game_type = f'R{rubber_number}'  # Use R1, R2, R3... instead of MD1, WD1, XD1
            
            # Cell 1: Home players (nested table)
            home_player_names = []
            home_table = cells[1].find('table')
            if home_table:
                player_links = home_table.find_all('a')
                for link in player_links:
                    player_name = link.get_text(strip=True)
                    player_name = re.sub(r'\s*\([^)]*\)$', '', player_name)
                    home_player_names.append(player_name)
            
            # Cell 3: Away players (nested table)
            away_player_names = []
            away_table = cells[3].find('table')
            if away_table:
                player_links = away_table.find_all('a')
                for link in player_links:
                    player_name = link.get_text(strip=True)
                    player_name = re.sub(r'\s*\([^)]*\)$', '', player_name)
                    away_player_names.append(player_name)
            
            # Cell 4: Score
            score_text = None
            score_span = cells[4].find('span', class_='score')
            if score_span:
                set_spans = score_span.find_all('span')
                set_scores = [span.get_text(strip=True) for span in set_spans]
                score_text = ' '.join(set_scores) if set_scores else score_span.get_text(strip=True)
            
            # Store in flattened format
            match_row[f'{game_type}_Home_P1'] = home_player_names[0] if len(home_player_names) > 0 else None
            match_row[f'{game_type}_Home_P2'] = home_player_names[1] if len(home_player_names) > 1 else None
            match_row[f'{game_type}_Away_P1'] = away_player_names[0] if len(away_player_names) > 0 else None
            match_row[f'{game_type}_Away_P2'] = away_player_names[1] if len(away_player_names) > 1 else None
            match_row[f'{game_type}_Score'] = score_text
        
        game_count = len([k for k in match_row.keys() if k.endswith('_Score') and match_row[k] is not None])
        logger.info(f"Parsed match {match_id}: {game_count} games found")
    
    except Exception as e:
        logger.error(f"Error parsing match details for match {match_id}: {str(e)}")
    
    return match_row
