#!/usr/bin/env python3
"""
Generate award images for Badminton Wrapped.

This script queries the mart_club_awards table and generates
shareable award images for each player at a specified club.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import duckdb
from PIL import Image, ImageDraw, ImageFont, ImageColor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Image dimensions (Instagram Story / WhatsApp Story format)
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1920

# Color scheme (darker background with neon accents)
COLOR_GRADIENT_START = "#0a0a0a"  # Very dark grey/black
COLOR_GRADIENT_END = "#1a1a2e"    # Dark blue-grey
COLOR_TEXT_PRIMARY = "#FFFFFF"     # White
COLOR_TEXT_SECONDARY = "#FFFFFF"   # White
COLOR_ACCENT = "#FFFFFF"           # White
COLOR_NET = "#FF6B35"              # Neon orange

# Typography sizes
FONT_SIZE_TITLE = 88
FONT_SIZE_PLAYER = 120
FONT_SIZE_VALUE = 180
FONT_SIZE_DETAIL = 42
FONT_SIZE_SUBTITLE = 58


class AwardImageGenerator:
    """Generate award images for badminton players."""
    
    def __init__(self, db_path: str, output_dir: str):
        """
        Initialize the generator.
        
        Args:
            db_path: Path to the DuckDB database
            output_dir: Directory to save generated images
        """
        self.db_path = Path(db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to load fonts (fallback to default if not available)
        self.fonts = self._load_fonts()
        
    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts for the images."""
        fonts = {}
        
        # Try to load system fonts (macOS paths) - prioritize bold fonts
        font_paths = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/SFCompactDisplay-Bold.otf",
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSDisplay.ttf",
            "/Library/Fonts/Arial.ttf",
        ]
        
        try:
            # Try to find a suitable font
            for font_path in font_paths:
                if Path(font_path).exists():
                    fonts['title'] = ImageFont.truetype(font_path, FONT_SIZE_TITLE)
                    fonts['player'] = ImageFont.truetype(font_path, FONT_SIZE_PLAYER)
                    fonts['value'] = ImageFont.truetype(font_path, FONT_SIZE_VALUE)
                    fonts['detail'] = ImageFont.truetype(font_path, FONT_SIZE_DETAIL)
                    fonts['subtitle'] = ImageFont.truetype(font_path, FONT_SIZE_SUBTITLE)
                    logger.info(f"Loaded fonts from: {font_path}")
                    break
            else:
                raise FileNotFoundError("No suitable font found")
                
        except Exception as e:
            logger.warning(f"Could not load system fonts: {e}. Using default font.")
            # Fallback to default
            fonts['title'] = ImageFont.load_default()
            fonts['player'] = ImageFont.load_default()
            fonts['value'] = ImageFont.load_default()
            fonts['detail'] = ImageFont.load_default()
            fonts['subtitle'] = ImageFont.load_default()
            
        return fonts
    
    def _create_gradient_background(self, width: int, height: int) -> Image.Image:
        """Create a vertical gradient background."""
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Parse colors
        start_color = ImageColor.getrgb(COLOR_GRADIENT_START)
        end_color = ImageColor.getrgb(COLOR_GRADIENT_END)
        
        # Create gradient
        for y in range(height):
            # Calculate interpolated color
            ratio = y / height
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        return image
    
    def _draw_racket_silhouette(self, draw: ImageDraw.Draw, width: int, height: int):
        """Draw a semi-transparent badminton racket silhouette in the background."""
        # Racket dimensions (large, centered)
        racket_head_width = 420
        racket_head_height = 500
        handle_width = 25
        handle_length = 480
        
        # Position (centered, slightly offset)
        center_x = width // 2
        center_y = height // 2 - 100
        
        # Racket head (oval)
        head_left = center_x - racket_head_width // 2
        head_top = center_y - racket_head_height // 2
        head_right = center_x + racket_head_width // 2
        head_bottom = center_y + racket_head_height // 2
        
        # Semi-transparent white
        racket_color = (255, 255, 255, 25)  # Very subtle
        
        # Create a temporary image with alpha channel for transparency
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Draw racket head outline (thick)
        for i in range(15):
            overlay_draw.ellipse(
                [head_left - i, head_top - i, head_right + i, head_bottom + i],
                outline=racket_color
            )
        
        # Draw strings (grid pattern inside oval)
        string_color = (255, 255, 255, 15)
        num_strings = 12
        
        # Vertical strings
        for i in range(num_strings):
            x = head_left + (i * (racket_head_width // num_strings))
            overlay_draw.line([(x, head_top), (x, head_bottom)], fill=string_color, width=2)
        
        # Horizontal strings
        for i in range(num_strings):
            y = head_top + (i * (racket_head_height // num_strings))
            overlay_draw.line([(head_left, y), (head_right, y)], fill=string_color, width=2)
        
        # Draw handle
        handle_top = head_bottom
        handle_bottom = handle_top + handle_length
        handle_left = center_x - handle_width // 2
        handle_right = center_x + handle_width // 2
        
        # Handle outline (thick)
        for i in range(15):
            overlay_draw.rectangle(
                [handle_left - i, handle_top, handle_right + i, handle_bottom],
                outline=racket_color
            )
        
        # Handle grip lines
        for i in range(8):
            y = handle_top + (i * (handle_length // 8))
            overlay_draw.line(
                [(handle_left - 15, y), (handle_right + 15, y)],
                fill=string_color,
                width=3
            )
        
        return overlay
    
    def _draw_badminton_net(self, width: int, height: int) -> Image.Image:
        """Draw a badminton net at the bottom with neon orange gradient fading out."""
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Net parameters
        net_height = 400  # Height of net from bottom
        net_start_y = height - net_height
        net_cord_thickness = 12  # Thick cord at top
        
        # Parse neon orange color
        net_color = ImageColor.getrgb(COLOR_NET)
        
        # Draw thick net cord at the top (fully opaque)
        for i in range(net_cord_thickness):
            y = net_start_y + i
            overlay_draw.line([(0, y), (width, y)], fill=(*net_color, 220), width=1)
        
        # Draw horizontal net lines with gradient fade (starting below the cord)
        num_horizontal_lines = 15
        for i in range(num_horizontal_lines):
            y = net_start_y + net_cord_thickness + (i * ((net_height - net_cord_thickness) // num_horizontal_lines))
            # Calculate alpha based on position (fade from top to bottom)
            alpha = int(180 * (1 - (y - net_start_y) / net_height))  # Fades to 0
            line_color = (*net_color, alpha)
            overlay_draw.line([(0, y), (width, y)], fill=line_color, width=6)
        
        # Draw vertical net lines with gradient fade
        num_vertical_lines = 20
        for i in range(num_vertical_lines + 1):
            x = i * (width // num_vertical_lines)
            for y in range(net_start_y, height, 2):
                # Calculate alpha based on position (fade from top to bottom)
                alpha = int(180 * (1 - (y - net_start_y) / net_height))
                line_color = (*net_color, alpha)
                overlay_draw.point((x, y), fill=line_color)
                if x > 0:  # Make lines thicker
                    overlay_draw.point((x-1, y), fill=line_color)
                    overlay_draw.point((x+1, y), fill=line_color)
        
        return overlay
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """Wrap text to fit within a maximum width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _format_award_name(self, award: str) -> str:
        """Convert award identifier to display name."""
        award_names = {
            'most_comebacks': 'Comeback King',
            'most_deuce_wins': 'Deuce Master',
            'biggest_comeback_points': 'Greatest Comeback',
            'most_clean_sweeps': 'Domination Award',
            'club_stalwart': 'Club Stalwart',
            'no_mercy': 'No Mercy',
            'performs_under_pressure': 'Performs Under Pressure',
            'longest_winning_streak': 'Longest Winning Streak',
            'defensive_wall': 'Defensive Wall',
            'giant_killing': 'Giant Slayer',
            'epic_win': 'Epic Win',
            'clean_sweep_specialist': 'Clean Sweep Specialist',
            'perfect_partnership': 'Perfect Partnership',
        }
        return award_names.get(award, award.replace('_', ' ').title())
    
    def _get_award_explanation(self, award: str) -> str:
        """Get a brief explanation for each award type."""
        explanations = {
            'most_comebacks': 'Won after losing the first game',
            'club_stalwart': 'Most dedicated club player',
            'performs_under_pressure': 'Master of narrow victories',
            'longest_winning_streak': 'Unstoppable winning run',
            'defensive_wall': 'Fewest points conceded',
            'giant_killing': 'Beat opponents from higher divisions',
            'no_mercy': 'Biggest 2-game demolition',
            'epic_win': 'Highest-scoring 3-game thriller',
            'clean_sweep_specialist': 'Dominant 2-0 rubber wins',
            'perfect_partnership': 'Unbeatable partnership',
        }
        return explanations.get(award, '')
    
    def _format_award_value_text(self, award: str, value: int) -> str:
        """Format the award value with appropriate context."""
        if award == 'most_comebacks':
            return "Comebacks" if value != 1 else "Comeback"
        elif award == 'most_deuce_wins':
            return "Deuce Wins" if value != 1 else "Deuce Win"
        elif award == 'biggest_comeback_points':
            return "Point Comeback"
        elif award == 'most_clean_sweeps':
            return "Clean Sweeps" if value != 1 else "Clean Sweep"
        elif award == 'club_stalwart':
            return "Matches Played" if value != 1 else "Match Played"
        elif award == 'no_mercy':
            return "Point Margin" if value != 1 else "Point Margin"
        elif award == 'performs_under_pressure':
            return "2-Point Wins" if value != 1 else "2-Point Win"
        elif award == 'longest_winning_streak':
            return "Consecutive Wins" if value != 1 else "Consecutive Win"
        elif award == 'defensive_wall':
            return "Avg Points Conceded"
        elif award == 'giant_killing':
            return "Division" + ("s" if value != 1 else "") + " Higher"
        elif award == 'epic_win':
            return "Total Points Scored"
        elif award == 'clean_sweep_specialist':
            return "Clean Sweeps" if value != 1 else "Clean Sweep"
        elif award == 'perfect_partnership':
            return "Wins Together" if value != 1 else "Win Together"
        else:
            return ""
    
    def _parse_award_details(self, details: str, max_items: int = 3) -> List[str]:
        """Parse and format award details for display."""
        if not details:
            return []
        
        # Split by pipe delimiter
        matches = details.split('|')
        
        # Format and limit to max_items
        formatted = []
        for i, match in enumerate(matches):
            match = match.strip()
            # For stalwart award, show all stats (not truncated)
            if 'Played in' in match or 'Played ' in match or 'Total points' in match:
                formatted.append(f"• {match}")
            else:
                # Shorten other awards if too long (remove score details)
                if len(match) > 120:
                    # Extract date and opponent
                    parts = match.split(':')
                    if len(parts) >= 2:
                        date_part = parts[0].strip()
                        opponent_part = parts[1].split('(')[0].strip()
                        match = f"{date_part}: {opponent_part}"
                formatted.append(f"• {match}")
                
                # Limit other awards to max_items
                if i >= max_items - 1:
                    break
        
        # Add "and X more..." if there are more matches (but not for stalwart)
        if len(matches) > max_items and 'Played in' not in details:
            remaining = len(matches) - max_items
            formatted.append(f"• ...and {remaining} more")
        
        return formatted
    
    def create_award_image(
        self,
        player: str,
        club: str,
        award: str,
        award_value: int,
        award_details: str,
        output_path: Path,
        player_2: str = None
    ) -> None:
        """
        Create an award image for a player or partnership.
        
        Args:
            player: Primary player name
            club: Club name
            award: Award type
            award_value: Award metric value
            award_details: Detailed award information
            output_path: Path to save the image
            player_2: Secondary player name for partnership awards (optional)
        """
        # Create base image with gradient
        img = self._create_gradient_background(IMAGE_WIDTH, IMAGE_HEIGHT)
        
        # Add racket silhouette overlay
        racket_overlay = self._draw_racket_silhouette(None, IMAGE_WIDTH, IMAGE_HEIGHT)
        img = Image.alpha_composite(img.convert('RGBA'), racket_overlay)
        
        # Add badminton net at bottom
        net_overlay = self._draw_badminton_net(IMAGE_WIDTH, IMAGE_HEIGHT)
        img = Image.alpha_composite(img, net_overlay).convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        # Layout parameters
        margin = 80
        current_y = margin
        
        # 1. Season text at top
        season_text = "2024-25 Season"
        bbox = self.fonts['subtitle'].getbbox(season_text)
        season_width = bbox[2] - bbox[0]
        season_x = (IMAGE_WIDTH - season_width) // 2
        
        draw.text(
            (season_x, current_y),
            season_text,
            font=self.fonts['subtitle'],
            fill=COLOR_TEXT_SECONDARY
        )
        current_y += 100
        
        # 2. Club name
        bbox = self.fonts['subtitle'].getbbox(club)
        club_width = bbox[2] - bbox[0]
        club_x = (IMAGE_WIDTH - club_width) // 2
        
        draw.text(
            (club_x, current_y),
            club,
            font=self.fonts['subtitle'],
            fill=COLOR_ACCENT
        )
        current_y += 100
        
        # 3. Player name(s) - handle partnership awards
        max_width = IMAGE_WIDTH - (2 * margin)
        
        if player_2:  # Partnership award - display both names with "&"
            # Format as "Player 1 & Player 2"
            partnership_text = f"{player} & {player_2}"
            player_lines = self._wrap_text(partnership_text, self.fonts['player'], max_width)
        else:  # Individual award - single player
            player_lines = self._wrap_text(player, self.fonts['player'], max_width)
        
        for line in player_lines:
            bbox = self.fonts['player'].getbbox(line)
            line_width = bbox[2] - bbox[0]
            line_x = (IMAGE_WIDTH - line_width) // 2
            
            draw.text(
                (line_x, current_y),
                line,
                font=self.fonts['player'],
                fill=COLOR_TEXT_PRIMARY
            )
            current_y += 110
        
        current_y += 60
        
        # 4. Award name
        award_name = self._format_award_name(award)
        bbox = self.fonts['subtitle'].getbbox(award_name)
        award_name_width = bbox[2] - bbox[0]
        award_name_x = (IMAGE_WIDTH - award_name_width) // 2
        
        draw.text(
            (award_name_x, current_y),
            award_name,
            font=self.fonts['subtitle'],
            fill=COLOR_TEXT_SECONDARY
        )
        current_y += 80
        
        # 5. Award explanation
        explanation = self._get_award_explanation(award)
        if explanation:
            bbox = self.fonts['detail'].getbbox(explanation)
            explanation_width = bbox[2] - bbox[0]
            explanation_x = (IMAGE_WIDTH - explanation_width) // 2
            
            draw.text(
                (explanation_x, current_y),
                explanation,
                font=self.fonts['detail'],
                fill=COLOR_TEXT_SECONDARY
            )
            current_y += 100
        
        # 6. Award value (big number)
        value_text = str(award_value)
        bbox = self.fonts['value'].getbbox(value_text)
        value_width = bbox[2] - bbox[0]
        value_x = (IMAGE_WIDTH - value_width) // 2
        
        draw.text(
            (value_x, current_y),
            value_text,
            font=self.fonts['value'],
            fill=COLOR_ACCENT
        )
        current_y += 160
        
        # 7. Award value context
        value_context = self._format_award_value_text(award, award_value)
        bbox = self.fonts['subtitle'].getbbox(value_context)
        context_width = bbox[2] - bbox[0]
        context_x = (IMAGE_WIDTH - context_width) // 2
        
        draw.text(
            (context_x, current_y),
            value_context,
            font=self.fonts['subtitle'],
            fill=COLOR_TEXT_SECONDARY
        )
        current_y += 120
        
        # 8. Award details (top matches)
        if award_details:
            detail_lines = self._parse_award_details(award_details, max_items=3)
            
            for detail_line in detail_lines:
                # Wrap long lines
                wrapped_lines = self._wrap_text(
                    detail_line,
                    self.fonts['detail'],
                    IMAGE_WIDTH - (2 * margin)
                )
                
                for wrapped_line in wrapped_lines:
                    draw.text(
                        (margin, current_y),
                        wrapped_line,
                        font=self.fonts['detail'],
                        fill=COLOR_TEXT_SECONDARY
                    )
                    current_y += 50
        
        # Save image
        img.save(output_path, 'PNG', optimize=True)
        logger.info(f"Created award image: {output_path}")
    
    def query_club_awards(self, club: str) -> List[Dict]:
        """
        Query awards for a specific club.
        
        Args:
            club: Club name to filter by
            
        Returns:
            List of award dictionaries
        """
        try:
            conn = duckdb.connect(str(self.db_path), read_only=True)
            
            query = """
                SELECT
                    award,
                    club,
                    player,
                    player_2,
                    award_value,
                    award_details
                FROM mart_club_awards
                WHERE club = ?
                ORDER BY award, award_value DESC
            """
            
            result = conn.execute(query, [club]).fetchall()
            conn.close()
            
            if not result:
                logger.warning(f"No awards found for club: {club}")
                return []
            
            # Convert to list of dicts
            awards = []
            for row in result:
                awards.append({
                    'award': row[0],
                    'club': row[1],
                    'player': row[2],
                    'player_2': row[3],
                    'award_value': row[4],
                    'award_details': row[5]
                })
            
            logger.info(f"Found {len(awards)} award(s) for club: {club}")
            return awards
            
        except Exception as e:
            logger.error(f"Error querying database: {e}")
            raise
    
    def generate_images_for_club(self, club: str) -> int:
        """
        Generate all award images for a club.
        
        Args:
            club: Club name
            
        Returns:
            Number of images generated
        """
        # Query awards
        awards = self.query_club_awards(club)
        
        if not awards:
            logger.info(f"No awards to generate for club: {club}")
            return 0
        
        # Generate images
        for award_data in awards:
            # Create filename - use both player names for pairs
            player_slug = award_data['player'].lower().replace(' ', '_')
            award_slug = award_data['award']
            
            if award_data['player_2']:  # Partnership award
                player2_slug = award_data['player_2'].lower().replace(' ', '_')
                filename = f"{player_slug}_and_{player2_slug}_{award_slug}.png"
            else:  # Individual award
                filename = f"{player_slug}_{award_slug}.png"
            
            output_path = self.output_dir / filename
            
            # Create image
            self.create_award_image(
                player=award_data['player'],
                player_2=award_data['player_2'],
                club=award_data['club'],
                award=award_data['award'],
                award_value=award_data['award_value'],
                award_details=award_data['award_details'],
                output_path=output_path
            )
        
        logger.info(f"Generated {len(awards)} award image(s) for {club}")
        return len(awards)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate Badminton Wrapped award images for a club'
    )
    parser.add_argument(
        '--club',
        required=True,
        help='Club name to generate awards for'
    )
    parser.add_argument(
        '--db-path',
        default='../data/badminton_wrapped.duckdb',
        help='Path to DuckDB database (default: ../data/badminton_wrapped.duckdb)'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory for images (default: ../data/processed/award_images/{club_name}/)'
    )
    
    args = parser.parse_args()
    
    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        club_slug = args.club.lower().replace(' ', '_')
        output_dir = f'../data/processed/award_images/{club_slug}'
    
    # Create generator
    generator = AwardImageGenerator(
        db_path=args.db_path,
        output_dir=output_dir
    )
    
    # Generate images
    try:
        num_images = generator.generate_images_for_club(args.club)
        print(f"\n✅ Successfully generated {num_images} award image(s) for {args.club}")
        print(f"📁 Images saved to: {Path(output_dir).resolve()}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate images: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
