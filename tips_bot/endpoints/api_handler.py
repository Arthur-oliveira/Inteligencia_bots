import requests
import pandas as pd
from io import StringIO
from database.database_manager import log

# Endpoints e URLs
URL_BY_ATHLETE = "https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/statistics/byathlete?isqualified=true&limit=50&sort=offensive.avgPoints:desc"
URL_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
URL_TEAM_BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
URL_SCRAPE_INJURIES = "https://www.espn.com/nba/injuries"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_league_rankings():
    """Busca os 50 melhores atletas da liga (API)."""
    try:
        response = requests.get(URL_BY_ATHLETE, timeout=15)
        response.raise_for_status()
        return response.json().get('athletes', [])
    except Exception as e:
        log.error(f"Erro na API Rankings: {e}")
        return []

def get_scoreboard():
    """Busca os jogos do dia (API)."""
    try:
        response = requests.get(URL_SCOREBOARD, timeout=15)
        response.raise_for_status()
        return response.json().get('events', [])
    except Exception as e:
        log.error(f"Erro na API Scoreboard: {e}")
        return []

def get_team_schedule(team_id):
    """
    Busca histórico para cálculo de médias dos últimos jogos (API).
    RESTORED: Esta função é essencial para o cálculo de médias.
    """
    try:
        url = f"{URL_TEAM_BASE}/{team_id}/schedule"
        response = requests.get(url, timeout=10)
        return response.json().get('events', [])
    except Exception as e:
        log.error(f"Erro na API Schedule {team_id}: {e}")
        return []

def get_all_injured_players():
    """
    VARREDURA DE LESÕES VIA SCRAPING (FONTE REAL).
    Retorna lista de dicionários: [{'player_name': 'Nikola Jokic', 'status': 'Out', ...}]
    """
    injured_list = []
    try:
        log.info(f"🕵️ Iniciando Scraping de Lesões em: {URL_SCRAPE_INJURIES}")
        response = requests.get(URL_SCRAPE_INJURIES, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # Leitura das tabelas HTML com Pandas
        dfs = pd.read_html(StringIO(response.text))
        
        if not dfs:
            log.warning("⚠️ Scraping realizado, mas nenhuma tabela encontrada.")
            return []
            
        for df in dfs:
            # Padroniza colunas para maiúsculo
            df.columns = [str(c).upper() for c in df.columns]
            
            if 'NAME' in df.columns and 'STATUS' in df.columns:
                for _, row in df.iterrows():
                    raw_name = str(row['NAME'])
                    status = str(row['STATUS'])
                    date_val = str(row['DATE']) if 'DATE' in df.columns else ''
                    
                    injured_list.append({
                        "player_name": raw_name.strip(),
                        "status": status.strip(),
                        "details": date_val.strip()
                    })
                    
        return injured_list

    except Exception as e:
        log.error(f"❌ Erro fatal no Scraping de lesões: {e}")
        return []