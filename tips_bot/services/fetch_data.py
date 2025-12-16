# C:\inteligencia_bots\tips_bot\services\fetch_data.py
import requests
import pandas as pd
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguedashplayerstats, teamgamelog

# Endpoints ESPN
URL_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
URL_INJURIES = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
CURRENT_SEASON = '2025-26'

def buscar_lesoes():
    try:
        print("🚑 Buscando relatório de lesões (ESPN)...")
        resp = requests.get(URL_INJURIES, headers=HEADERS)
        data = resp.json()
        lesionados = {}
        for team in data.get("injuries", []):
            for athlete in team.get("athletes", []):
                nome = athlete.get("displayName", "").lower()
                status = athlete.get("status", "Unknown")
                lesionados[nome] = status
        return lesionados
    except Exception as e:
        print(f"⚠️ Erro ao buscar lesões: {e}")
        return {}

def buscar_jogos_hoje():
    try:
        print("🏀 Buscando jogos do dia (ESPN Scoreboard)...")
        resp = requests.get(URL_SCOREBOARD, headers=HEADERS)
        data = resp.json()
        jogos = []
        for event in data.get("events", []):
            status = event.get("status", {}).get("type", {}).get("state")
            if status != "post": 
                comp = event["competitions"][0]
                competitors = comp["competitors"]
                mandante = next(t for t in competitors if t["homeAway"] == "home")
                visitante = next(t for t in competitors if t["homeAway"] == "away")
                jogos.append({
                    "game_id": event["id"],
                    "data_jogo": event["date"],
                    "mandante_nome": mandante["team"]["displayName"],
                    "visitante_nome": visitante["team"]["displayName"]
                })
        print(f"✅ Encontrados {len(jogos)} jogos.")
        return jogos
    except Exception as e:
        print(f"❌ Erro scoreboard: {e}")
        return []

def get_nba_team_id(team_name):
    mapa_nomes = {"LA Clippers": "L.A. Clippers", "Los Angeles Clippers": "L.A. Clippers"}
    busca = mapa_nomes.get(team_name, team_name)
    nba_teams = teams.get_teams()
    found = [t for t in nba_teams if t['full_name'].lower() == busca.lower()]
    if found: return found[0]['id']
    found_partial = [t for t in nba_teams if busca.lower() in t['full_name'].lower()]
    return found_partial[0]['id'] if found_partial else None

def analisar_estatisticas_time(team_name_espn):
    """
    Retorna Média 3 Jogos + Top 2 Cestinhas com PPG.
    """
    try:
        team_id = get_nba_team_id(team_name_espn)
        if not team_id:
            return {"media_3_jogos": 0.0, "cestinhas": []}

        # 1. Média Recente (Últimos 3 jogos)
        gamelog = teamgamelog.TeamGameLog(team_id=team_id, season=CURRENT_SEASON)
        df_games = gamelog.get_data_frames()[0]
        media_pts = 0.0
        if not df_games.empty:
            media_pts = df_games.head(3)['PTS'].mean()

        # 2. Top Scorers com PPG (Points Per Game)
        player_stats = leaguedashplayerstats.LeagueDashPlayerStats(
            team_id_nullable=team_id,
            per_mode_detailed='PerGame', 
            season=CURRENT_SEASON
        )
        df_players = player_stats.get_data_frames()[0]
        df_players = df_players.sort_values(by='PTS', ascending=False)
        
        cestinhas_list = []
        if not df_players.empty:
            # Pegamos os 2 primeiros
            top2 = df_players.head(2)
            for _, row in top2.iterrows():
                cestinhas_list.append({
                    "nome": row['PLAYER_NAME'],
                    "ppg": float(row['PTS'])
                })
        
        # Completa com N/A se faltar jogador
        while len(cestinhas_list) < 2:
            cestinhas_list.append({"nome": "N/A", "ppg": 0.0})

        return {
            "media_3_jogos": float(media_pts),
            "cestinhas": cestinhas_list # [{'nome': '...', 'ppg': 25.4}, ...]
        }

    except Exception as e:
        print(f"❌ Erro NBA API ({team_name_espn}): {e}")
        # Retorno seguro em caso de falha
        return {"media_3_jogos": 0.0, "cestinhas": [{"nome": "N/A", "ppg": 0.0}, {"nome": "N/A", "ppg": 0.0}]}