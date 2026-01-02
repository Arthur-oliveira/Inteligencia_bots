# C:\inteligencia_bots\tips_bot\services\fetch_data.py
import requests
from datetime import datetime, timedelta
from dateutil import parser
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguedashplayerstats, teamgamelog

URL_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
URL_INJURIES = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
HEADERS = {"User-Agent": "Mozilla/5.0"}
CURRENT_SEASON = '2025-26'

def buscar_jogos_hoje():
    try:
        resp = requests.get(URL_SCOREBOARD, headers=HEADERS).json()
        jogos = []
        for event in resp.get("events", []):
            if event.get("status", {}).get("type", {}).get("state") != "post":
                comp = event["competitions"][0]
                m = next(t for t in comp["competitors"] if t["homeAway"] == "home")
                v = next(t for t in comp["competitors"] if t["homeAway"] == "away")
                dt = parser.parse(event["date"]) - timedelta(hours=3)
                jogos.append({
                    "game_id": event["id"], "mandante_nome": m["team"]["displayName"],
                    "visitante_nome": v["team"]["displayName"], "hora": dt.strftime("%H:%M")
                })
        return jogos
    except: return []

def analisar_estatisticas_time(team_name):
    try:
        nba_teams = teams.get_teams()
        team_id = [t for t in nba_teams if team_name.lower() in t['full_name'].lower()][0]['id']
        gl = teamgamelog.TeamGameLog(team_id=team_id, season=CURRENT_SEASON).get_data_frames()[0]
        media = gl.head(3)['PTS'].mean() if not gl.empty else 0.0
        ps = leaguedashplayerstats.LeagueDashPlayerStats(team_id_nullable=team_id, per_mode_detailed='PerGame', season=CURRENT_SEASON).get_data_frames()[0]
        ps = ps.sort_values(by='PTS', ascending=False).head(2)
        cestinhas = [{"nome": row['PLAYER_NAME'], "ppg": float(row['PTS'])} for _, row in ps.iterrows()]
        while len(cestinhas) < 2: cestinhas.append({"nome": "N/A", "ppg": 0.0})
        return {"media_3_jogos": float(media), "cestinhas": cestinhas}
    except:
        return {"media_3_jogos": 0.0, "cestinhas": [{"nome": "N/A", "ppg": 0.0}, {"nome": "N/A", "ppg": 0.0}]}

def buscar_lesoes():
    try:
        data = requests.get(URL_INJURIES, headers=HEADERS).json()
        les = {}
        for t in data.get("injuries", []):
            for a in t.get("athletes", []):
                les[a.get("displayName", "").lower()] = a.get("status", "Unknown")
        return les
    except: return {}