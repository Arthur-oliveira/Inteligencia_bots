import requests
from database.database_manager import log

# Endpoints Oficiais ESPN 2025/26
URL_BY_ATHLETE = "https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/statistics/byathlete?isqualified=true&limit=50&sort=offensive.avgPoints:desc"
URL_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
URL_TEAM_BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"

def get_league_rankings():
    """Busca os 50 melhores atletas da liga em tempo real."""
    try:
        response = requests.get(URL_BY_ATHLETE, timeout=15)
        response.raise_for_status()
        return response.json().get('athletes', [])
    except Exception as e:
        log.error(f"Erro na API Rankings: {e}")
        return []

def get_scoreboard():
    """Busca os jogos do dia."""
    try:
        response = requests.get(URL_SCOREBOARD, timeout=15)
        response.raise_for_status()
        return response.json().get('events', [])
    except Exception as e:
        log.error(f"Erro na API Scoreboard: {e}")
        return []

def get_team_schedule(team_id):
    """Busca histórico para cálculo de médias dos últimos 3 jogos."""
    try:
        url = f"{URL_TEAM_BASE}/{team_id}/schedule"
        response = requests.get(url, timeout=10)
        return response.json().get('events', [])
    except Exception as e:
        log.error(f"Erro na API Schedule {team_id}: {e}")
        return []