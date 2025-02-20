import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def fetch_laliga_matches():
    """
    Fetches LaLiga matches (played and upcoming) from laliga.com.
    (Note: The CSS selectors here are examples and may need to be adjusted according
    to the actual HTML structure of the website.)
    """
    url = "https://www.laliga.com/en-GB"  # Adjust URL as needed
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Error fetching LaLiga matches: {e}")
        return []
    
    soup = BeautifulSoup(response.content, "html.parser")
    matches = []
    # Example selector: adjust according to the actual page structure
    for match_div in soup.select(".match"):
        try:
            home_team = match_div.select_one('.home-team').get_text(strip=True)
            away_team = match_div.select_one('.away-team').get_text(strip=True)
            date_text = match_div.select_one('.match-date').get_text(strip=True)
            try:
                match_date = datetime.strptime(date_text, "%d/%m/%Y %H:%M")
            except Exception:
                match_date = date_text  # fallback if date format is different
            score_elem = match_div.select_one('.score')
            score = score_elem.get_text(strip=True) if score_elem else None
            matches.append({
                "home_team": home_team,
                "away_team": away_team,
                "date": match_date,
                "score": score,
            })
        except Exception as e:
            logger.warning(f"Error parsing a match div: {e}")
    return matches

def fetch_laliga_league_table():
    """
    Fetches the LaLiga league table from laliga.com.
    """
    url = "https://www.laliga.com/en-GB/table"  # Adjust URL if needed
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Error fetching LaLiga league table: {e}")
        return []
    
    soup = BeautifulSoup(response.content, "html.parser")
    table = []
    # Example selectors; adjust based on the actual HTML structure
    for row in soup.select("table.league-table tbody tr"):
        cols = row.find_all("td")
        if len(cols) < 4:
            continue
        position = cols[0].get_text(strip=True)
        team = cols[1].get_text(strip=True)
        played = cols[2].get_text(strip=True)
        points = cols[3].get_text(strip=True)
        table.append({
            "position": position,
            "team": team,
            "played": played,
            "points": points,
        })
    return table

def fetch_laliga_player_stats():
    """
    Fetches LaLiga player statistics from laliga.com.
    """
    url = "https://www.laliga.com/en-GB/statistics/players"  # Adjust URL if needed
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Error fetching LaLiga player statistics: {e}")
        return []
    
    soup = BeautifulSoup(response.content, "html.parser")
    players = []
    # Example selector; adjust based on the actual player statistics table
    for row in soup.select("table.player-stats tbody tr"):
        cols = row.find_all("td")
        if len(cols) < 4:
            continue
        name = cols[0].get_text(strip=True)
        team = cols[1].get_text(strip=True)
        goals = cols[2].get_text(strip=True)
        assists = cols[3].get_text(strip=True)
        players.append({
            "name": name,
            "team": team,
            "goals": goals,
            "assists": assists,
        })
    return players 