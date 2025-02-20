from models import CachedPlayer, Player


import logging
import requests
from datetime import datetime, timedelta
from flask import render_template, jsonify, request
from flask import current_app as app
from abilities import upload_file_to_storage, url_for_uploaded_file
from models import db, AppSettings
from bs4 import BeautifulSoup
from seriea import fetch_seriea_matches, fetch_seriea_league_table, fetch_seriea_player_stats
from laliga import fetch_laliga_matches, fetch_laliga_league_table, fetch_laliga_player_stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_routes(app):
    @app.route('/gameweek')
    def gameweek():
        try:
            # Get current gameweek data from FPL API
            response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
            if response.status_code != 200:
                logger.error(f"Failed to fetch FPL data. Status code: {response.status_code}")
                return render_template('gameweek.html', error="Failed to fetch gameweek data")
            
            data = response.json()
            
            # Get current gameweek
            current_gameweek = next((event['id'] for event in data['events'] if event['is_current']), 1)
            
            # Get team data for mapping
            teams_data = {team['id']: {
                'name': team['name'],
                'code': team['code']
            } for team in data['teams']}
            
            # Process player data
            players = data['elements']
            processed_players = []
            
            for player in players:
                team_info = teams_data.get(player['team'], {'name': 'Unknown', 'code': 0})
                position = {
                    1: 'Goalkeeper',
                    2: 'Defender',
                    3: 'Midfielder',
                    4: 'Forward'
                }.get(player['element_type'], 'Unknown')
                
                processed_player = {
                    'id': player['id'],
                    'name': f"{player['first_name']} {player['second_name']}",
                    'team': team_info['name'],
                    'position': position,
                    'photo_url': f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{player.get('code', '')}.png",
                    'minutes': player.get('minutes', 0),
                    'goals_scored': player.get('goals_scored', 0),
                    'assists': player.get('assists', 0),
                    'clean_sheets': player.get('clean_sheets', 0),
                    'bonus': player.get('bonus', 0),
                    'team_logo': f"https://resources.premierleague.com/premierleague/badges/t{team_info['code']}.png",
                    'points': player['event_points'],
                    'transfers_in': player['transfers_in_event'],
                    'transfers_out': player['transfers_out_event']
                }
                processed_players.append(processed_player)
            
            # Get player of the week from FPL API
            current_event = next((event for event in data['events'] if event['is_current']), None)
            if not current_event:
                logger.error("No current gameweek found")
                return render_template('gameweek.html', error="No current gameweek found")
            
            top_player_id = current_event.get('top_element')
            if not top_player_id:
                logger.error("No top player found for current gameweek")
                return render_template('gameweek.html', error="No top player found")
            
            player_of_week = next((p for p in players if p['id'] == top_player_id), None)
            if not player_of_week or player_of_week['element_type'] not in [1, 2, 3, 4]:
                logger.error(f"Player with ID {top_player_id} not found in elements or is not a valid player type")
                return render_template('gameweek.html', error="Top player details not found or invalid player type")
            
            # Update player details for rendering
            player_of_week['photo_url'] = f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{player_of_week.get('code', '')}.png"
            player_of_week['team_logo'] = f"https://resources.premierleague.com/premierleague/badges/t{teams_data[player_of_week['team']]['code']}.png"
            player_of_week['name'] = f"{player_of_week['first_name']} {player_of_week['second_name']}"
            player_of_week['team'] = teams_data[player_of_week['team']]['name']
            
            # Get the last match details for player of the week
            player_details = fetch_player_details(player_of_week['id'])
            if player_details['success'] and player_details['history']:
                last_match = player_details['history'][-1]  # Get the most recent match
                player_of_week['last_match'] = last_match
            else:
                # Fallback to current stats if history is not available
                player_of_week['last_match'] = {
                    'opponent': 'N/A',
                    'score': 'N/A',
                    'result': '',
                    'minutes': player_of_week.get('minutes', 0),
                    'goals_scored': player_of_week.get('goals_scored', 0),
                    'assists': player_of_week.get('assists', 0),
                    'clean_sheets': player_of_week.get('clean_sheets', 0),
                    'bonus': player_of_week.get('bonus', 0),
                    'total_points': player_of_week.get('points', 0)
                }

            # Get team of the week data
            team_of_week = {
                'Goalkeeper': [],
                'Defender': [],
                'Midfielder': [],
                'Forward': []
            }
            
            # Sort players by event points and process by position
            sorted_players = sorted(
                [p for p in data['elements'] if p.get('event_points', 0) > 0],
                key=lambda x: (x['event_points'], x.get('goals_scored', 0), x.get('assists', 0), x.get('bonus', 0)),
                reverse=True
            )
            
            for player in sorted_players:
                position = {
                    1: 'Goalkeeper',
                    2: 'Defender',
                    3: 'Midfielder',
                    4: 'Forward'
                }.get(player['element_type'])
                
                if position and len(team_of_week[position]) < (1 if position == 'Goalkeeper' else 4 if position in ['Defender', 'Midfielder'] else 2):
                    player_team_info = teams_data.get(player['team'])
                    if not player_team_info:
                        logger.warning(f"Team info not found for player {player['id']}")
                        continue
                    
                    team_of_week[position].append({
                        'id': player['id'],
                        'name': f"{player['first_name']} {player['second_name']}",
                        'team': player_team_info['name'],
                        'position': position,
                        'points': player['event_points'],
                        'photo_url': f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{player['code']}.png",
                        'team_logo': f"https://resources.premierleague.com/premierleague/badges/t{player_team_info['code']}.png",
                        'minutes': player.get('minutes', 0),
                        'goals_scored': player.get('goals_scored', 0),
                        'assists': player.get('assists', 0),
                        'clean_sheets': player.get('clean_sheets', 0),
                        'bonus': player.get('bonus', 0)
                    })
            
            # Get top transfers
            transfers_in = sorted(
                [p for p in data['elements'] if p['element_type'] in [1, 2, 3, 4]], 
                key=lambda x: x.get('transfers_in_event', 0), 
                reverse=True
            )[:5]
            
            transfers_out = sorted(
                [p for p in data['elements'] if p['element_type'] in [1, 2, 3, 4]], 
                key=lambda x: x.get('transfers_out_event', 0), 
                reverse=True
            )[:5]
            
            # Process transfers in data
            processed_transfers_in = []
            for p in transfers_in:
                try:
                    team_id = int(p['team'])
                except Exception as e:
                    logger.warning(f"Error converting team id for transfer player {p['id']}: {str(e)}")
                    team_id = p['team']
                player_team_info = teams_data.get(team_id, {'name': 'Unknown', 'code': 0})
                processed_transfers_in.append({
                    'id': p['id'],
                    'name': f"{p['first_name']} {p['second_name']}",
                    'team': player_team_info['name'],
                    'position': {1: 'Goalkeeper', 2: 'Defender', 3: 'Midfielder', 4: 'Forward'}.get(p['element_type'], 'Unknown'),
                    'transfers_in': p.get('transfers_in_event', 0),
                    'photo_url': f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{p['code']}.png",
                    'team_logo': f"https://resources.premierleague.com/premierleague/badges/t{player_team_info['code']}.png"
                })
            
            processed_transfers_out = []
            for p in transfers_out:
                try:
                    team_id = int(p['team'])
                except Exception as e:
                    logger.warning(f"Error converting team id for transfer player {p['id']}: {str(e)}")
                    team_id = p['team']
                player_team_info = teams_data.get(team_id, {'name': 'Unknown', 'code': 0})
                processed_transfers_out.append({
                    'id': p['id'],
                    'name': f"{p['first_name']} {p['second_name']}",
                    'team': player_team_info['name'],
                    'position': {1: 'Goalkeeper', 2: 'Defender', 3: 'Midfielder', 4: 'Forward'}.get(p['element_type'], 'Unknown'),
                    'transfers_out': p.get('transfers_out_event', 0),
                    'photo_url': f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{p['code']}.png",
                    'team_logo': f"https://resources.premierleague.com/premierleague/badges/t{player_team_info['code']}.png"
                })
            
            return render_template('gameweek.html',
                                  current_gameweek=current_gameweek,
                                  player_of_week=player_of_week,
                                  team_of_week=team_of_week,
                                  transfers_in=processed_transfers_in,
                                  transfers_out=processed_transfers_out,
                                  logo_url=get_logo_url())
            
        except Exception as e:
            logger.error(f"Error in gameweek route: {str(e)}")
            return render_template('gameweek.html', error="Failed to load gameweek data")
    
    @app.route('/fixtures')
    def fixtures():
        return render_template('fixtures.html', logo_url=get_logo_url())
    
    @app.route('/api/fixtures', methods=['GET'])
    def get_fixtures():
        """Get fixtures data with optional gameweek filter"""
        try:
            # Get gameweek filter from query parameters
            gameweek = request.args.get('gameweek', type=int)
            logger.info(f"Fetching Premier League fixtures{' for gameweek ' + str(gameweek) if gameweek else ''}...")
            
            # Use Premier League's API
            url = 'https://fantasy.premierleague.com/api/fixtures/'
            response = requests.get(url)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch fixtures. Status code: {response.status_code}")
                return jsonify({'success': False, 'error': 'Failed to fetch fixtures'}), 500
            
            fixtures_data = response.json()
            
            # Filter fixtures by gameweek if provided
            if gameweek:
                fixtures_data = [f for f in fixtures_data if f['event'] == gameweek]
            
            # Get team data for mapping team IDs to names and logos
            bootstrap_response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
            bootstrap_response.raise_for_status()
            teams_data = {team['id']: {
                'name': team['name'],
                'logo': f"https://resources.premierleague.com/premierleague/badges/t{team['code']}.png"
            } for team in bootstrap_response.json()['teams']}
            
            processed_fixtures = []
            for fixture in fixtures_data:
                try:
                    home_team = teams_data.get(fixture['team_h'], {'name': 'Unknown', 'logo': ''})
                    away_team = teams_data.get(fixture['team_a'], {'name': 'Unknown', 'logo': ''})
                    
                    # Format the date and time
                    if fixture['kickoff_time']:
                        date_str, time_str = format_fixture_date(fixture['kickoff_time'])
                        kickoff_time = f"{date_str} | {time_str}"
                    else:
                        kickoff_time = 'TBD'
                    
                    fixture_data = {
                        'id': fixture['id'],
                        'gameweek': fixture['event'],
                        'kickoff_time': kickoff_time,
                        'team_h': home_team['name'],
                        'team_h_logo': home_team['logo'],
                        'team_a': away_team['name'],
                        'team_a_logo': away_team['logo'],
                        'team_h_score': fixture['team_h_score'] if fixture['started'] else None,
                        'team_a_score': fixture['team_a_score'] if fixture['started'] else None,
                        'started': fixture['started'],
                        'finished': fixture['finished']
                    }
                    
                    processed_fixtures.append(fixture_data)
                except Exception as e:
                    logger.error(f"Error processing fixture: {str(e)}")
                    continue
            
            # Sort fixtures by kickoff time
            processed_fixtures.sort(key=lambda x: (
                x['kickoff_time'] if x['kickoff_time'] != 'TBD' else '9999-12-31'
            ))
            
            return jsonify({
                'success': True,
                'fixtures': processed_fixtures
            })
        except Exception as e:
            logger.error(f"Error fetching fixtures: {str(e)}")
            return jsonify({'success': False, 'error': 'Failed to fetch fixtures'}), 500
    
    @app.route('/api/gameweek')
    def api_gameweek():
        try:
            # Fetch gameweek data from FPL API
            response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
            response.raise_for_status()
            data = response.json()
            
            logger.info("Successfully fetched FPL bootstrap data")
            
            # Get current gameweek
            current_gameweek = next((event['id'] for event in data['events'] if event['is_current']), 1)
            
            # Get team data for mapping
            teams_data = {team['id']: {
                'name': team['name'],
                'code': team['code'],
                'short_name': team['short_name']
            } for team in data['teams']}
            
            # First, get the current gameweek's highest scoring player from FPL API
            current_gameweek = next((event['id'] for event in data['events'] if event['is_current']), 1)
            
            # Get team data for mapping
            teams_data = {team['id']: {
                'name': team['name'],
                'code': team['code'],
                'short_name': team['short_name']
            } for team in data['teams']}
            
            # Get all players and their event points
            players = data['elements']
            
            # First, filter out managers and non-players
            actual_players = [p for p in players if p.get('element_type', 0) in [1, 2, 3, 4]]
            
            # Log all players with points for debugging
            for p in actual_players:
                event_points = p.get('event_points', 0)
                if event_points > 0:
                    logger.info(
                        f"Player: {p.get('first_name')} {p.get('second_name')} - "
                        f"Points: {event_points}, "
                        f"Type: {p.get('element_type')}, "
                        f"Goals: {p.get('goals_scored', 0)}, "
                        f"Assists: {p.get('assists', 0)}, "
                        f"Bonus: {p.get('bonus', 0)}, "
                        f"Team: {teams_data.get(p.get('team', 0), {}).get('name', 'Unknown')}"
                    )
            
            # Sort players by minutes played (descending)
            sorted_players = sorted(
                actual_players,
                key=lambda x: (
                    x.get('minutes', 0),
                    x.get('goals_scored', 0),
                    x.get('assists', 0),
                    x.get('bonus', 0)
                ),
                reverse=True
            )
            
            # Get the current gameweek's highest scoring player
            current_event = next((event for event in data['events'] if event['is_current']), None)
            if not current_event:
                logger.error("No current gameweek found")
                return jsonify({'success': False, 'error': 'No current gameweek found'}), 500
            
            # Get the top scorer for the current gameweek
            top_player_id = current_event.get('top_element')
            if not top_player_id:
                logger.error("No top player found for current gameweek")
                return jsonify({'success': False, 'error': 'No top player found'}), 500
            
            # Find the player details from the elements list
            player_of_week = next((p for p in data['elements'] if p['id'] == top_player_id and p['element_type'] in [1, 2, 3, 4]), None)
            if not player_of_week:
                logger.error(f"Player with ID {top_player_id} not found in elements or is not a valid player type")
                return jsonify({'success': False, 'error': 'Top player details not found or invalid player type'}), 500
            
            logger.info(
                f"Selected player of the week from FPL API: {player_of_week['first_name']} {player_of_week['second_name']} - "
                f"Points: {player_of_week['event_points']}, "
                f"Type: {player_of_week['element_type']}, "
                f"Goals: {player_of_week.get('goals_scored', 0)}, "
                f"Assists: {player_of_week.get('assists', 0)}, "
                f"Bonus: {player_of_week.get('bonus', 0)}"
            )
            
            # Get team info for player of the week
            team_info = teams_data.get(player_of_week['team'])
            if not team_info:
                logger.error(f"Team info not found for player {player_of_week['id']}")
                team_info = {'name': 'Unknown', 'code': 0, 'short_name': 'UNK'}
            
            # Get player details including last match
            player_details = fetch_player_details(player_of_week['id'])
            last_match = {}
            if player_details['success'] and player_details['history']:
                last_match = player_details['history'][-1]
            
            # Process team of the week by position using event_points sorting
            team_of_week = {
                'Goalkeeper': [],
                'Defender': [],
                'Midfielder': [],
                'Forward': []
            }

            sorted_players = sorted(
                [p for p in players if p.get('event_points', 0) > 0],
                key=lambda x: (x['event_points'], x.get('goals_scored', 0), x.get('assists', 0), x.get('bonus', 0)),
                reverse=True
            )

            for player in sorted_players:
                position = {1: 'Goalkeeper', 2: 'Defender', 3: 'Midfielder', 4: 'Forward'}.get(player['element_type'])
                if not position:
                    continue

                # Formation limits: 1 GK, 4 DEF, 4 MID, 2 FWD
                limit = 1 if position == 'Goalkeeper' else 4 if position in ['Defender', 'Midfielder'] else 2
                if len(team_of_week[position]) < limit:
                    player_team_info = teams_data.get(player['team'], {'name': 'Unknown', 'code': 0})
                    team_of_week[position].append({
                        'id': player['id'],
                        'name': f"{player['first_name']} {player['second_name']}",
                        'team': player_team_info['name'],
                        'position': position,
                        'points': player['event_points'],
                        'photo_url': f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{player['code']}.png",
                        'team_logo': f"https://resources.premierleague.com/premierleague/badges/t{player_team_info['code']}.png",
                        'minutes': player.get('minutes', 0),
                        'goals_scored': player.get('goals_scored', 0),
                        'assists': player.get('assists', 0),
                        'clean_sheets': player.get('clean_sheets', 0),
                        'bonus': player.get('bonus', 0)
                    })
            
            # Get top transfers
            transfers_in = sorted(players, key=lambda x: x.get('transfers_in_event', 0), reverse=True)[:5]
            transfers_out = sorted(players, key=lambda x: x.get('transfers_out_event', 0), reverse=True)[:5]
            
            # Process transfers in data
            processed_transfers_in = []
            for p in transfers_in:
                try:
                    team_id = int(p['team'])
                except Exception as e:
                    logger.warning(f"Error converting team id for transfer player {p['id']}: {str(e)}")
                    team_id = p['team']
                player_team_info = teams_data.get(team_id, {'name': 'Unknown', 'code': 0})
                processed_transfers_in.append({
                    'id': p['id'],
                    'name': f"{p['first_name']} {p['second_name']}",
                    'team': player_team_info['name'],
                    'position': {1: 'Goalkeeper', 2: 'Defender', 3: 'Midfielder', 4: 'Forward'}.get(p['element_type'], 'Unknown'),
                    'transfers_in': p.get('transfers_in_event', 0),
                    'photo_url': f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{p['code']}.png",
                    'team_logo': f"https://resources.premierleague.com/premierleague/badges/t{player_team_info['code']}.png"
                })
            
            # Process transfers out data
            processed_transfers_out = []
            for p in transfers_out:
                try:
                    team_id = int(p['team'])
                except Exception as e:
                    logger.warning(f"Error converting team id for transfer player {p['id']}: {str(e)}")
                    team_id = p['team']
                player_team_info = teams_data.get(team_id, {'name': 'Unknown', 'code': 0})
                processed_transfers_out.append({
                    'id': p['id'],
                    'name': f"{p['first_name']} {p['second_name']}",
                    'team': player_team_info['name'],
                    'position': {1: 'Goalkeeper', 2: 'Defender', 3: 'Midfielder', 4: 'Forward'}.get(p['element_type'], 'Unknown'),
                    'transfers_out': p.get('transfers_out_event', 0),
                    'photo_url': f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{p['code']}.png",
                    'team_logo': f"https://resources.premierleague.com/premierleague/badges/t{player_team_info['code']}.png"
                })
            
            response_data = {
                'success': True,
                'current_gameweek': current_gameweek,
                'player_of_week': {
                    'id': player_of_week['id'],
                    'name': f"{player_of_week['first_name']} {player_of_week['second_name']}",
                    'team': team_info['name'],
                    'position': {1: 'Goalkeeper', 2: 'Defender', 3: 'Midfielder', 4: 'Forward'}.get(player_of_week['element_type'], 'Unknown'),
                    'points': player_of_week['event_points'],
                    'photo_url': f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{player_of_week['code']}.png",
                    'team_logo': f"https://resources.premierleague.com/premierleague/badges/t{team_info['code']}.png",
                    'last_match': last_match
                },
                'team_of_week': team_of_week,
                'transfers': {
                    'in': processed_transfers_in,
                    'out': processed_transfers_out
                }
            }
            
            logger.info(f"Successfully processed gameweek data for week {current_gameweek}")
            return jsonify(response_data)
        except Exception as e:
            logger.error(f"Error fetching gameweek data: {str(e)}")
            return jsonify({'success': False, 'error': 'Failed to fetch gameweek data'}), 500
    
    @app.route('/')
    def home():
        return render_template('home.html', logo_url=get_logo_url())
    
    @app.route('/api/endpoint')
    def api_endpoint():
        """Endpoint for API documentation"""
        host_url = request.host_url.rstrip('/')
        return jsonify({
            'success': True,
            'message': 'API endpoint is available',
            'endpoints': {
                'players': f'{host_url}/api/players',
                'player_details': f'{host_url}/api/player/<player_id>/details',
                'league_table': f'{host_url}/api/table',
                'batch_details': f'{host_url}/api/players/batch-details',
                'players_json': f'{host_url}/api/players/json',
                'fixtures': f'{host_url}/api/fixtures',
                'gameweek': {
                    'url': f'{host_url}/api/gameweek',
                    'description': 'Get current gameweek data including Player of the Week, Team of the Week, and transfer trends',
                    'response_format': {
                        'success': 'boolean',
                        'current_gameweek': 'integer',
                        'player_of_week': {
                            'id': 'integer',
                            'name': 'string',
                            'team': 'string',
                            'position': 'string',
                            'points': 'integer',
                            'photo_url': 'string',
                            'team_logo': 'string',
                            'last_match': 'object with match statistics'
                        },
                        'team_of_week': {
                            'Goalkeeper': 'array of player objects',
                            'Defender': 'array of player objects',
                            'Midfielder': 'array of player objects',
                            'Forward': 'array of player objects'
                        },
                        'transfers': {
                            'in': 'array of top 5 transferred in players',
                            'out': 'array of top 5 transferred out players'
                        }
                    }
                }
            }
        })
    
    @app.route('/table')
    def league_table():
        return render_template('table.html', logo_url=get_logo_url())
    
    @app.route('/api/table')
    def get_league_table():
        try:
            logger.info("Fetching Premier League table data...")
            
            # Use Premier League's website
            url = 'https://www.premierleague.com/tables'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1'
            }
            
            logger.info("Making request to Premier League website...")
            response = requests.get(url, headers=headers)
            logger.info(f"Response Status Code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch table data. Status code: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                return jsonify({'success': False, 'error': 'Failed to fetch league table'}), 500
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info("Successfully parsed HTML content")
            
            # Try different selectors for the Premier League table
            table_selectors = [
                'table.league-table',
                'table.statsTable',
                'div[data-competition-id="1"] table',
                '#mainContent table'
            ]
            
            table = None
            for selector in table_selectors:
                table = soup.select_one(selector)
                if table:
                    logger.info(f"Found table using selector: {selector}")
                    break
            
            if not table:
                logger.error("Could not find Premier League table")
                logger.error(f"Available tables: {[t.get('class', []) for t in soup.find_all('table')]}")
                return jsonify({'success': False, 'error': 'No table data found'}), 500
            
            # Try different selectors for table rows
            row_selectors = [
                'tr:not(.expandable)',
                'tr.league-table__row:not(.league-table__row--sub)',
                'tr[data-filtered-table-row]'
            ]
            
            table_rows = []
            for selector in row_selectors:
                table_rows = table.select(selector)
                if table_rows:
                    logger.info(f"Found {len(table_rows)} rows using selector: {selector}")
                    break
            
            if not table_rows:
                logger.error("No Premier League table rows found")
                logger.error(f"Table HTML: {table}")
                return jsonify({'success': False, 'error': 'No table data found'}), 500
            
            table_data = []
            for row in table_rows:
                try:
                    # Try different selectors for team name and badge
                    team_name_selectors = [
                        '.league-table__team-name',
                        '.team-name',
                        'td:nth-child(2) span',
                        'td:nth-child(2) a'
                    ]
                    
                    team_badge_selectors = [
                        '.league-table__team-badge',
                        '.badge-25',
                        'td:nth-child(2) img',
                        '.team-badge'
                    ]
                    
                    team_name_elem = None
                    for selector in team_name_selectors:
                        team_name_elem = row.select_one(selector)
                        if team_name_elem:
                            break
                    
                    team_badge_elem = None
                    for selector in team_badge_selectors:
                        team_badge_elem = row.select_one(selector)
                        if team_badge_elem:
                            break
                    
                    if not team_name_elem or not team_badge_elem:
                        logger.error(f"Missing team info in row: {row}")
                        continue
                    
                    team_name = team_name_elem.text.strip()
                    team_badge = team_badge_elem.get('src', team_badge_elem.get('data-src', ''))
                    
                    # Get numeric stats
                    stats = row.select('td')
                    if len(stats) < 10:
                        logger.error(f"Not enough stats in row: {row}")
                        continue
                    
                    # Extract numeric values, skipping the first two columns (position and team name)
                    numeric_stats = []
                    for stat in stats[2:10]:  # Get played, won, drawn, lost, GF, GA, GD, points
                        try:
                            value = int(stat.text.strip())
                            numeric_stats.append(value)
                        except ValueError:
                            logger.error(f"Invalid numeric value in stats: {stat.text}")
                            break
                    
                    if len(numeric_stats) != 8:
                        logger.error(f"Invalid number of stats for {team_name}: {numeric_stats}")
                        continue
                    
                    team_data = {
                        'name': team_name,
                        'logo': team_badge,
                        'played': numeric_stats[0],
                        'won': numeric_stats[1],
                        'drawn': numeric_stats[2],
                        'lost': numeric_stats[3],
                        'goals_for': numeric_stats[4],
                        'goals_against': numeric_stats[5],
                        'goal_difference': numeric_stats[6],
                        'points': numeric_stats[7]
                    }
                    table_data.append(team_data)
                    logger.info(f"Processed team data: {team_name}")
                except Exception as e:
                    logger.error(f"Error processing team row: {str(e)}")
                    logger.error(f"Row HTML: {row}")
                    continue
            
            if not table_data:
                logger.error("No team data was extracted")
                return jsonify({'success': False, 'error': 'No team data found'}), 500
            
            logger.info(f"Successfully compiled table data for {len(table_data)} teams")
            return jsonify({
                'success': True,
                'table': table_data
            })
        except Exception as e:
            logger.error(f"Error fetching league table: {str(e)}")
            return jsonify({'success': False, 'error': 'Failed to fetch league table'}), 500
    
    @app.route('/compare')
    def compare_players():
        try:
            players = Player.query.order_by(Player.name).all()
            return render_template('compare.html', players=players, logo_url=get_logo_url())
        except Exception as e:
            logger.error(f"Error loading players for comparison: {str(e)}")
            return render_template('compare.html', players=[], logo_url=get_logo_url())

    @app.route('/api/players/json', methods=['GET'])
    def get_players_json():
        """Endpoint for getting player data with current sorting, filtering, detailed match history and form"""
        """Endpoint for getting player data with current sorting and filtering"""
        def fetch_player_details_async(player_id):
            try:
                details = fetch_player_details(player_id)
                return details if details.get('success') else None
            except Exception as e:
                logger.error(f"Error fetching details for player {player_id}: {str(e)}")
                return None
        
        try:
            # Get all parameters from the request
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            position = request.args.get('position')
            team = request.args.get('team')
            max_price = request.args.get('max_price', type=float)
            min_points = request.args.get('min_points', type=int)
            sort_column = request.args.get('sort_column', type=int)
            sort_direction = request.args.get('sort_direction') == 'true'
            
            # Get all players from FPL API first
            fpl_data = fetch_fpl_data()
            if not fpl_data or not fpl_data.get('elements'):
                logger.error("Failed to fetch FPL data")
                return jsonify({
                    'success': False,
                    'message': 'Failed to fetch player data',
                    'players': [],
                })
            
            # Apply the same sorting and filtering as the table
            filtered_players = fpl_data['elements']
            
            # Apply filters exactly as in the frontend
            if position:
                filtered_players = [p for p in filtered_players if p['position'] == position]
            if team:
                filtered_players = [p for p in filtered_players if p['team'] == team]
            if max_price:
                filtered_players = [p for p in filtered_players if float(p['price']) <= max_price]
            if min_points:
                filtered_players = [p for p in filtered_players if int(p['total_points']) >= min_points]
            
            # Apply sorting using the same logic as the frontend
            if sort_column is not None:
                sort_key = None
                if sort_column == 0:  # Player name
                    sort_key = 'name'
                elif sort_column == 1:  # Team
                    sort_key = 'team'
                elif sort_column == 2:  # Price
                    sort_key = 'price'
                elif sort_column == 3:  # Total Points
                    sort_key = 'total_points'
                elif sort_column == 4:  # Event Points
                    sort_key = 'event_points'
                elif sort_column == 5:  # Minutes played
                    sort_key = 'minutes'
                elif sort_column == 6:  # Goals scored
                    sort_key = 'goals_scored'
                elif sort_column == 7:  # Assists
                    sort_key = 'assists'
                elif sort_column == 8:  # Expected goals
                    sort_key = 'expected_goals'
                elif sort_column == 9:  # Expected assists
                    sort_key = 'expected_assists'
                elif sort_column == 10:  # Clean sheets
                    sort_key = 'clean_sheets'
                elif sort_column == 11:  # Goals conceded
                    sort_key = 'goals_conceded'
                elif sort_column == 12:  # Expected goals conceded
                    sort_key = 'expected_goals_conceded'
                elif sort_column == 13:  # Own goals
                    sort_key = 'own_goals'
                elif sort_column == 14:  # Penalties saved
                    sort_key = 'penalties_saved'
                elif sort_column == 15:  # Penalties missed
                    sort_key = 'penalties_missed'
                elif sort_column == 16:  # Yellow cards
                    sort_key = 'yellow_cards'
                elif sort_column == 17:  # Red cards
                    sort_key = 'red_cards'
                elif sort_column == 18:  # Saves
                    sort_key = 'saves'
                elif sort_column == 19:  # Bonus
                    sort_key = 'bonus'
                elif sort_column == 20:  # BPS
                    sort_key = 'bps'
                elif sort_column == 21:  # Influence
                    sort_key = 'influence'
                elif sort_column == 22:  # Creativity
                    sort_key = 'creativity'
                elif sort_column == 23:  # Threat
                    sort_key = 'threat'
                elif sort_column == 24:  # ICT index
                    sort_key = 'ict_index'
                elif sort_column == 25:  # Selected by percent
                    sort_key = 'selected_by_percent'
                
                if sort_key:
                    filtered_players.sort(
                        key=lambda x: (float(x[sort_key]) if isinstance(x.get(sort_key), (int, float, str)) else 0),
                        reverse=sort_direction
                    )
            
            # Get the players for the current page
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            current_page_players = filtered_players[start_idx:end_idx]
            
            players_data = []
            for player in current_page_players:
                try:
                    # Fetch player details including history and fixtures
                    details = fetch_player_details(player['id'])
                    
                    player_data = {
                        'id': player['id'],
                        'name': player['name'],
                        'position': player['position'],
                        'photo_url': player['photo_url'],
                        'team': player['team'],
                        'team_logo': player['team_logo'],
                        'price': f"£{player['price']}m",
                        'form': float(player.get('form', 0)),
                        'total_points': int(player['total_points']),
                        'event_points': int(player.get('event_points', 0)),
                        'minutes': int(player['minutes']),
                        'goals_scored': int(player['goals_scored']),
                        'assists': int(player['assists']),
                        'expected_goals': float(player['expected_goals']),
                        'expected_assists': float(player['expected_assists']),
                        'clean_sheets': int(player['clean_sheets']),
                        'goals_conceded': int(player['goals_conceded']),
                        'expected_goals_conceded': float(player['expected_goals_conceded']),
                        'own_goals': int(player['own_goals']),
                        'penalties_saved': int(player['penalties_saved']),
                        'penalties_missed': int(player['penalties_missed']),
                        'yellow_cards': int(player['yellow_cards']),
                        'red_cards': int(player['red_cards']),
                        'saves': int(player['saves']),
                        'bonus': int(player['bonus']),
                        'bps': int(player['bps']),
                        'influence': float(player['influence']),
                        'creativity': float(player['creativity']),
                        'threat': float(player['threat']),
                        'ict_index': float(player['ict_index']),
                        'selected_by_percent': float(player['selected_by_percent']),
                        'upcoming_fixtures': details.get('fixtures', []) if details and details.get('success') else [],
                        'recent_matches': details.get('history', []) if details and details.get('success') else []
                    }
                    players_data.append(player_data)
                except Exception as e:
                    logger.error(f"Error processing player data: {str(e)}")
                    continue
            
            if not players_data:
                return jsonify({
                    'success': False,
                    'error': 'No player data found'
                }), 500
            
            return jsonify({
                'success': True,
                'players': players_data,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_players': len(filtered_players),
                    'total_pages': max(1, (len(filtered_players) + per_page - 1) // per_page)
                }
            })
        except Exception as e:
            logger.error(f"Error getting players JSON: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}',
                'players': []
            })

    @app.route('/api/players/batch-details', methods=['POST'])
    def get_batch_player_details():
        try:
            player_ids = request.json.get('player_ids', [])
            if not player_ids:
                return jsonify({'success': False, 'error': 'No player IDs provided'}), 400
            
            players_details = []
            for player_id in player_ids:
                player_details = fetch_player_details(player_id)
                if player_details['success']:
                    players_details.append(player_details)
                else:
                    logger.warning(f"Failed to fetch details for player ID: {player_id}")
            
            return jsonify({
                'success': True,
                'players': players_details
            })
        except Exception as e:
            logger.error(f"Error fetching batch player details: {str(e)}")
            return jsonify({'success': False, 'error': 'Failed to fetch batch player details'}), 500

    # Team of the week API endpoint removed
    
    @app.route('/api/players')
    def get_players():
        try:
            data = fetch_fpl_data()
            if not data:
                return jsonify({'success': False, 'error': 'Failed to fetch player data'}), 500
            
            last_updated = datetime.utcnow()
            return jsonify({
                'success': True,
                'players': data['elements'],
                'last_updated': last_updated.isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting players: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/players/compare')
    def compare_players_api():
        try:
            # Check for name search parameter
            search_name = request.args.get('name', '').lower()
            if search_name:
                data = fetch_fpl_data()
                if not data or not data.get('elements'):
                    return jsonify({'success': False, 'error': 'Failed to fetch player data'}), 500
                
                # Search for players by name
                matching_players = [
                    p for p in data['elements']
                    if search_name in p['name'].lower()
                ][:5]  # Limit to 5 results
                
                if not matching_players:
                    return jsonify({
                        'success': False,
                        'error': f'No players found matching "{search_name}"'
                    }), 404
                
                return jsonify({
                    'success': True,
                    'players': matching_players
                })
            
            # If no name search, proceed with ID-based comparison
            player_ids = request.args.get('player_ids', '')
            if not player_ids:
                return jsonify({'success': False, 'error': 'No player IDs provided'}), 400
            
            player_id_list = [int(pid) for pid in player_ids.split(',')]
            data = fetch_fpl_data()
            
            if not data or not data.get('elements'):
                return jsonify({'success': False, 'error': 'Failed to fetch player data'}), 500
            
            players = [p for p in data['elements'] if p['id'] in player_id_list]
            
            if not players:
                return jsonify({'success': False, 'error': 'No players found with the provided IDs'}), 404
            
            return jsonify({
                'success': True,
                'players': players
            })
            
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid player IDs provided'}), 400
        except Exception as e:
            logger.error(f"Error comparing players: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/player/<int:player_id>/details')
    def get_player_details(player_id):
        try:
            details = fetch_player_details(player_id)
            return jsonify(details)
        except Exception as e:
            logger.error(f"Error getting player details: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/upload-logo', methods=['POST'])
    def upload_logo():
        try:
            if 'logo' not in request.files:
                return jsonify({'success': False, 'error': 'No file provided'}), 400
            
            file = request.files['logo']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            
            if not file.content_type.startswith('image/'):
                return jsonify({'success': False, 'error': 'File must be an image'}), 400
            
            file_id = upload_file_to_storage(file)
            
            # Store the file ID in the database
            setting = AppSettings.query.filter_by(key='logo_file_id').first()
            if setting:
                setting.value = file_id
            else:
                setting = AppSettings(key='logo_file_id', value=file_id)
                db.session.add(setting)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'url': url_for_uploaded_file(file_id)
            })
            
        except Exception as e:
            logger.error(f"Error uploading logo: {str(e)}")
            return jsonify({'success': False, 'error': 'Failed to upload logo'}), 500

    @app.route('/api/export-sheets', methods=['POST'])
    def export_to_sheets():
        try:
            data = request.get_json()
            if not data or 'players' not in data:
                return jsonify({'success': False, 'error': 'No player data provided'}), 400
            
            # TODO: Add Google Sheets API integration
            # For now, return a mock URL to test the frontend
            spreadsheet_url = "https://docs.google.com/spreadsheets/d/example"
            
            return jsonify({
                'success': True,
                'spreadsheet_url': spreadsheet_url
            })
            
        except Exception as e:
            logger.error(f"Error exporting to sheets: {str(e)}")
            return jsonify({'success': False, 'error': 'Failed to export to Google Sheets'}), 500

    def get_logo_url():
        setting = AppSettings.query.filter_by(key='logo_file_id').first()
        if setting and setting.value:
            return url_for_uploaded_file(setting.value)
        return "https://storage.googleapis.com/lazy-icons/not-found-placeholder.webp"

    @app.route('/seriea')
    def seriea():
        player_stats = fetch_seriea_player_stats()

        # Update the Serie A players database with the scraped data
        from models import SerieAPlayer, db

        for p in player_stats:
            # Try to find an existing record by name
            player = SerieAPlayer.query.filter_by(name=p["name"]).first()
            if not player:
                player = SerieAPlayer(name=p["name"])
                db.session.add(player)

            # Update record with latest data
            player.team = p["team"]
            player.goals = int(p["goals"]) if p["goals"].isdigit() else 0
            player.assists = int(p["assists"]) if p["assists"].isdigit() else 0

        db.session.commit()

        logger.info(f"Scraped player stats: {player_stats}")

        return render_template('seriea.html', player_stats=player_stats)

    @app.route('/laliga')
    def laliga():
        try:
            matches = fetch_laliga_matches()
            league_table = fetch_laliga_league_table()
            player_stats = fetch_laliga_player_stats()
            return render_template("laliga.html",
                                   matches=matches,
                                   league_table=league_table,
                                   player_stats=player_stats,
                                   logo_url=get_logo_url())
        except Exception as e:
            logging.error(f"Error fetching LaLiga data: {e}")
            return render_template("laliga.html", error="Failed to fetch LaLiga data", logo_url=get_logo_url())

def format_fixture_date(utc_time_str):
    """Format fixture date to match FPL website format and convert to Maldives time"""
    try:
        if not utc_time_str:
            logger.warning("Empty UTC time string provided")
            return "TBD", ""
        
        utc_time = datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%SZ')
        # Convert to Maldives time (UTC+5)
        maldives_time = utc_time + timedelta(hours=5)
        logger.info(f"Converted to Maldives time: {maldives_time}")
        # Format the date part like "Wednesday 15 January 2024"
        date_str = maldives_time.strftime('%A %d %B %Y')
        # Format the time part like "20:00"
        time_str = maldives_time.strftime('%H:%M')
        return date_str, time_str
    except Exception as e:
        logger.error(f"Error formatting fixture date: {str(e)}")
        return utc_time_str, ""

def fetch_player_details(player_id):
    try:
        logger.info(f"Fetching details for player {player_id}")
        cached_data = CachedPlayer.get_cached_data(player_id)
        if cached_data:
            return {
                'success': True,
                'history': cached_data.get('history', []),
                'fixtures': cached_data.get('fixtures', [])
            }

        # Fetch player history
        history_response = requests.get(f'https://fantasy.premierleague.com/api/element-summary/{player_id}/')
        history_response.raise_for_status()
        history_data = history_response.json()
        
        # Get team data for mapping team codes to names
        bootstrap_response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
        bootstrap_response.raise_for_status()
        teams_data = {team['id']: team['name'] for team in bootstrap_response.json()['teams']}
        
        # Process history: iterate over all matches, then take the last 6 successfully processed entries
        processed_history = []
        fixtures = []  # Initialize fixtures list
        for match in history_data.get('history', []):
            try:
                opponent_team = teams_data.get(match['opponent_team'], 'Unknown')
                venue = '(H)' if match['was_home'] else '(A)'
                
                # Get the correct score based on venue
                if match['was_home']:
                    score = f"{match['team_h_score']}-{match['team_a_score']}"
                    result = 'W' if match['team_h_score'] > match['team_a_score'] else ('D' if match['team_h_score'] == match['team_a_score'] else 'L')
                else:
                    score = f"{match['team_a_score']}-{match['team_h_score']}"
                    result = 'W' if match['team_a_score'] > match['team_h_score'] else ('D' if match['team_a_score'] == match['team_h_score'] else 'L')
                
                match_data = {
                    'round': match['round'],
                    'opponent': f"{opponent_team} {venue} {score}",
                    'score': score,
                    'result': result,
                    'total_points': match['total_points'],
                    'minutes': match['minutes'],
                    'goals_scored': match['goals_scored'],
                    'assists': match['assists'],
                    'clean_sheets': match['clean_sheets'],
                    'bonus': match['bonus']
                }
                processed_history.append(match_data)
            except Exception as e:
                logger.error(f"Error processing match history: {str(e)}")
        history = processed_history[-6:]
        
        # Process fixtures (next 6 matches)
        for fixture in history_data.get('fixtures', [])[:6]:  # Get next 6 fixtures
            try:
                opponent_team = teams_data.get(fixture['team_a'] if fixture['is_home'] else fixture['team_h'], 'Unknown')
                venue = '(H)' if fixture['is_home'] else '(A)'
                
                # Handle missing kickoff time
                if fixture.get('kickoff_time'):
                    utc_time = datetime.strptime(fixture['kickoff_time'], '%Y-%m-%dT%H:%M:%SZ')
                    # Convert to Maldives time (UTC+5)
                    maldives_time = utc_time + timedelta(hours=5)
                    formatted_date = maldives_time.strftime('%a %d %b %H:%M')
                else:
                    formatted_date = 'TBD'
                
                fixture_data = {
                    'formatted_date': formatted_date,
                    'event': fixture['event'],
                    'opponent_name': f"{opponent_team} {venue}",
                    'difficulty': fixture['difficulty']
                }
                fixtures.append(fixture_data)
            except Exception as e:
                logger.error(f"Error processing fixture: {str(e)}")
                continue
        
        # Cache the data
        cache_data = {
            'history': history,
            'fixtures': fixtures
        }
        CachedPlayer.update_cache(player_id, cache_data)
        
        return {
            'success': True,
            'history': history,
            'fixtures': fixtures
        }
    except Exception as e:
        logger.error(f"Error fetching player details: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def fetch_fpl_data():
    try:
        # Use FPL API to get player data
        response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
        response.raise_for_status()
        data = response.json()
        
        # Get team data for mapping team codes to names
        teams_data = {team['id']: {
            'name': team['name'],
            'code': team['code']
        } for team in data['teams']}
        
        # Process all players
        players_data = []
        for player in data['elements']:
            try:
                team_info = teams_data.get(player['team'], {'name': 'Unknown', 'code': 0})
                position = {
                    1: 'Goalkeeper',
                    2: 'Defender',
                    3: 'Midfielder',
                    4: 'Forward'
                }.get(player['element_type'], 'Unknown')
                
                # Skip non-players
                if position == 'Unknown':
                    continue
                
                # Convert numeric values to proper types
                minutes = int(player.get('minutes', 0))
                goals_scored = int(player.get('goals_scored', 0))
                assists = int(player.get('assists', 0))
                clean_sheets = int(player.get('clean_sheets', 0))
                goals_conceded = int(player.get('goals_conceded', 0))
                own_goals = int(player.get('own_goals', 0))
                penalties_saved = int(player.get('penalties_saved', 0))
                penalties_missed = int(player.get('penalties_missed', 0))
                yellow_cards = int(player.get('yellow_cards', 0))
                red_cards = int(player.get('red_cards', 0))
                saves = int(player.get('saves', 0))
                bonus = int(player.get('bonus', 0))
                bps = int(player.get('bps', 0))
                total_points = int(player.get('total_points', 0))
                event_points = int(player.get('event_points', 0))
                form = float(player.get('form', 0))
                
                # Prepare player data
                player_data = {
                    'id': player.get('id', 0),
                    'name': f"{player.get('first_name', '')} {player.get('second_name', '')}",
                    'team': team_info['name'],
                    'position': position,
                    'photo_url': f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{player.get('code', '')}.png",
                    'team_logo': f"https://resources.premierleague.com/premierleague/badges/t{team_info['code']}.png",
                    'price': float(player.get('now_cost', 0)) / 10,
                    'minutes': minutes,
                    'goals_scored': goals_scored,
                    'assists': assists,
                    'expected_goals': float(player.get('expected_goals', 0) or 0),
                    'expected_assists': float(player.get('expected_assists', 0) or 0),
                    'clean_sheets': clean_sheets,
                    'goals_conceded': goals_conceded,
                    'expected_goals_conceded': float(player.get('expected_goals_conceded', 0) or 0),
                    'own_goals': own_goals,
                    'penalties_saved': penalties_saved,
                    'penalties_missed': penalties_missed,
                    'yellow_cards': yellow_cards,
                    'red_cards': red_cards,
                    'saves': saves,
                    'bonus': bonus,
                    'bps': bps,
                    'influence': float(player.get('influence', 0) or 0),
                    'creativity': float(player.get('creativity', 0) or 0),
                    'threat': float(player.get('threat', 0) or 0),
                    'ict_index': float(player.get('ict_index', 0) or 0),
                    'selected_by_percent': float(player.get('selected_by_percent', 0) or 0),
                    'form': form,
                    'points_per_match': float(player.get('points_per_game', 0) or 0),
                    'total_points': total_points,
                    'total_bonus': int(player.get('bonus', 0) or 0),
                    'event_points': event_points,
                    'starts': int(player.get('starts', 0) or 0),
                    'manager_wins': int(player.get('manager_wins', 0) or 0),
                    'manager_draws': int(player.get('manager_draws', 0) or 0),
                    'manager_losses': int(player.get('manager_losses', 0) or 0),
                    'manager_table_bonus_wins': int(player.get('manager_table_bonus_wins', 0) or 0),
                    'manager_table_bonus_draws': int(player.get('manager_table_bonus_draws', 0) or 0),
                    'manager_clean_sheets': int(player.get('manager_clean_sheets', 0) or 0),
                    'manager_goals_scored': int(player.get('manager_goals_scored', 0) or 0)
                }
                players_data.append(player_data)
            except Exception as e:
                logger.error(f"Error processing player data: {str(e)}")
                continue
        
        # Get sort parameters from request
        sort_column = request.args.get('sort_column', type=int)
        sort_direction = request.args.get('sort_direction') == 'true'
        
        # Sort players if sort parameters are provided
        if sort_column is not None:
            sort_key = None
            if sort_column == 0:  # Player name
                sort_key = 'name'
            elif sort_column == 1:  # Team
                sort_key = 'team'
            elif sort_column == 2:  # Price
                sort_key = 'price'
            elif sort_column == 3:  # Total points
                sort_key = 'total_points'
            elif sort_column == 4:  # Form
                sort_key = 'form'
            elif sort_column == 5:  # Event points
                sort_key = 'event_points'
            elif sort_column == 6:  # Minutes played
                sort_key = 'minutes'
            
            if sort_key:
                # Log sorting details
                logger.info(f"Sorting by {sort_key} in {'descending' if sort_direction else 'ascending'} order")
                
                # Sort players
                players_data.sort(
                    key=lambda x: (float(x.get(sort_key, 0)) if isinstance(x.get(sort_key), (int, float, str)) else 0),
                    reverse=sort_direction
                )
                
                # Log top 10 players after sorting
                logger.info("Top 10 players after sorting:")
                for i, p in enumerate(players_data[:10]):
                    logger.info(f"{i+1}. {p.get('name', '')} - {sort_key}: {p.get(sort_key, 0)}")
        
        return {'elements': players_data}
    except Exception as e:
        logger.error(f"Error fetching FPL data: {str(e)}")
        return None
    for player in players_data:
        try:
            details = fetch_player_details(player['id'])
            if details and details.get('success'):
                player['recent_matches'] = details.get('history', [])
                player['upcoming_fixtures'] = details.get('fixtures', [])
            else:
                player['recent_matches'] = []
                player['upcoming_fixtures'] = []
        except Exception as e:
            logger.error(f"Error fetching details for player {player['id']}: {str(e)}")
            player['recent_matches'] = []
            player['upcoming_fixtures'] = []