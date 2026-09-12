import difflib
import logging
import re

from . import db

logger = logging.getLogger(__name__)

# Cache all names from the database once to avoid repeated queries
_ALL_PLAYERS = None
_ALL_TEAMS = None
_ALL_VENUES = None

def _get_all_players():
    global _ALL_PLAYERS
    if _ALL_PLAYERS is None:
        _ALL_PLAYERS = db.get_all_player_names()
    return _ALL_PLAYERS

def _get_all_teams():
    global _ALL_TEAMS
    if _ALL_TEAMS is None:
        _ALL_TEAMS = db.get_all_team_names()
    return _ALL_TEAMS

def _get_all_venues():
    global _ALL_VENUES
    if _ALL_VENUES is None:
        _ALL_VENUES = db.get_all_venue_names()
    return _ALL_VENUES

def normalize_name(name: str) -> str:
    """Normalizes name by lowercase, stripping punctuation, and compressing spaces."""
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

def match_name(target: str, valid_names: list, entity_type: str) -> str:
    """
    Attempts to match the target name against valid_names using:
    1. Exact Match
    2. Normalized Match
    3. Conservative Fuzzy Match (cutoff=0.85)
    
    Returns the exact valid name if found, else None.
    """
    if not target:
        return None
        
    # 1. Exact Match
    if target in valid_names:
        return target
        
    # 2. Normalized Match
    target_norm = normalize_name(target)
    for name in valid_names:
        if target_norm == normalize_name(name):
            return name
            
    # 3. Conservative Fuzzy Match
    # 0.85 is a high threshold to prevent silly matches (e.g., matching "MS Dhoni" to "M Pandey")
    clean_names = [n for n in valid_names if isinstance(n, str)]
    matches = difflib.get_close_matches(target, clean_names, n=1, cutoff=0.85)
    if matches:
        matched = matches[0]
        logger.info(f"Fuzzy matched {entity_type} '{target}' to '{matched}'")
        return matched
        
    # No safe match found
    logger.warning(f"Unmatched {entity_type}: '{target}'")
    return None


def get_player_stats(target: str) -> dict:
    """Gets historical player stats, resolving name variations. Returns {} if unmatched."""
    matched = match_name(target, _get_all_players(), "player")
    if matched:
        return db.get_player_stats(matched) or {}
    return {}

def get_team_stats(target: str) -> dict:
    """Gets historical team stats, resolving name variations. Returns {} if unmatched."""
    matched = match_name(target, _get_all_teams(), "team")
    if matched:
        return db.get_team_stats(matched) or {}
    return {}

def get_venue_stats(target: str) -> dict:
    """Gets historical venue stats, resolving name variations. Returns {} if unmatched."""
    matched = match_name(target, _get_all_venues(), "venue")
    if matched:
        return db.get_venue_stats(matched) or {}
    return {}
