import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

logger = logging.getLogger(__name__)

def fetch_seriea_matches():
    """
    Fetches Serie A matches (played and upcoming) from legaseriea.it.
    (Note: The CSS selectors here are examples and may need to be adjusted according
    to the actual HTML structure of the league's website.)
    """
    url = "https://www.legaseriea.it/en"  # Adjust URL as needed
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Error fetching Serie A matches: {e}")
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
                match_date = date_text  # fallback to raw text
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

def fetch_seriea_league_table():
    """
    Fetches the Serie A league table from legaseriea.it.
    """
    url = "https://www.legaseriea.it/en/serie-a/classifica"  # Adjust URL if needed
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Error fetching Serie A league table: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    table = []
    # Example selectors; adjust based on the actual league table HTML structure
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

def fetch_seriea_player_stats():
    """
    Fetches Serie A player statistics from 
    [Lega Serie A Statistiche](https://www.legaseriea.it/en/serie-a/statistiche).
    Uses Selenium with WebDriver Manager to render JavaScript and scrape player stats.
    """
    url = "https://www.legaseriea.it/en/serie-a/statistiche"
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)

        # Wait until the relevant elements are present
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'player-stats')]"))
        )

        # Allow time for the page to load completely
        time.sleep(2)
        html = driver.page_source
        driver.quit()
    except Exception as e:
        logger.error(f"Error using Selenium to fetch Serie A player statistics: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    players = []

    # Find the relevant container for player statistics
    player_stats_container = soup.find("div", class_="player-stats")
    if not player_stats_container:
        logger.error("Player statistics container not found on Serie A statistics page")
        return []

    # Extract player data from the container
    for player_div in player_stats_container.find_all("div", class_="player"):
        player_name = player_div.find("span", class_="player-name").get_text(strip=True)
        player_team = player_div.find("span", class_="player-team").get_text(strip=True)
        player_goals = player_div.find("span", class_="player-goals").get_text(strip=True)
        player_assists = player_div.find("span", class_="player-assists").get_text(strip=True)

        players.append({
            "name": player_name,
            "team": player_team,
            "goals": player_goals,
            "assists": player_assists
        })

    return players 