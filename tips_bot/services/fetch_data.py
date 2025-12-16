# C:\inteligencia_bots\tips_bot\services\fetch_data.py
import requests
import statistics
from datetime import datetime

# Endpoints
URL_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
URL_INJURIES = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
URL_TEAMS = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"

# Header para simular navegador
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def buscar_lesoes():
    """
    Retorna dicionário: { 'lebron james': 'Day-to-Day', ... }
    """
    try:
        print("🚑 Buscando relatório geral de lesões...")
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
    """
    Busca os jogos do dia no Scoreboard.
    """
    try:
        print("🏀 Buscando jogos do dia...")
        resp = requests.get(URL_SCOREBOARD, headers=HEADERS)
        data = resp.json()
        
        jogos = []
        for event in data.get("events", []):
            status_jogo = event.get("status", {}).get("type", {}).get("state")
            
            # Filtra apenas jogos que ainda não começaram ("pre") ou estão acontecendo
            if status_jogo != "post": 
                comp = event["competitions"][0]
                competitors = comp["competitors"]
                
                mandante = next(t for t in competitors if t["homeAway"] == "home")
                visitante = next(t for t in competitors if t["homeAway"] == "away")
                
                jogos.append({
                    "game_id": event["id"],
                    "data_jogo": event["date"],
                    "mandante_nome": mandante["team"]["displayName"],
                    "mandante_id": mandante["team"]["id"],
                    "visitante_nome": visitante["team"]["displayName"],
                    "visitante_id": visitante["team"]["id"]
                })
            
        print(f"✅ Encontrados {len(jogos)} jogos para análise.")
        return jogos
    except Exception as e:
        print(f"❌ Erro ao buscar scoreboard: {e}")
        return []

def analisar_estatisticas_time(team_id):
    """
    1. Calcula média de pontos dos últimos 3 jogos.
    2. Identifica Top 2 cestinhas (Leaders).
    """
    media = 0.0
    top_scorers = []

    try:
        # --- A. Média Últimos 3 Jogos ---
        url_schedule = f"{URL_TEAMS}/{team_id}/schedule"
        resp_sched = requests.get(url_schedule, headers=HEADERS).json()
        
        events = resp_sched.get("events", [])
        jogos_finalizados = [
            ev for ev in events 
            if ev.get("competitions", [{}])[0].get("status", {}).get("type", {}).get("completed")
        ]
        
        ultimos_3 = jogos_finalizados[-3:]
        pontos_lista = []
        
        for jogo in ultimos_3:
            comp = jogo["competitions"][0]
            for competitor in comp["competitors"]:
                if str(competitor["id"]) == str(team_id):
                    score = int(competitor.get("score", {}).get("value", 0))
                    pontos_lista.append(score)
        
        if pontos_lista:
            media = statistics.mean(pontos_lista)

        # --- B. Principais Pontuadores (Leaders) ---
        url_leaders = f"{URL_TEAMS}/{team_id}?enable=leaders"
        resp_leaders = requests.get(url_leaders, headers=HEADERS).json()
        
        team_data = resp_leaders.get("team", {})
        leaders_groups = team_data.get("leaders", [])
        
        # DEBUG: Mostra o que a API retornou (ajuda a diagnosticar)
        nomes_cats = [g.get('name') for g in leaders_groups]
        # print(f"   ℹ️ Categorias encontradas time {team_id}: {nomes_cats}") # Descomente se quiser ver no log

        grupo_pontos = None
        
        # 1. Tenta achar pelo nome
        for group in leaders_groups:
            nome_grupo = group.get("name", "").lower()
            if "ppg" in nome_grupo or "points" in nome_grupo or "scoring" in nome_grupo or "offensive" in nome_grupo:
                grupo_pontos = group
                break
        
        # 2. PLANO B (Fallback): Se não achou pelo nome, pega o primeiro da lista
        if not grupo_pontos and leaders_groups:
            # Geralmente a primeira categoria é a principal (pontos)
            grupo_pontos = leaders_groups[0]
        
        if grupo_pontos:
            leaders_list = grupo_pontos.get("leaders", [])
            for player in leaders_list[:2]: # Pega Top 2
                nome = player.get("athlete", {}).get("displayName")
                top_scorers.append(nome)
        else:
            print(f"⚠️ Aviso: Nenhuma estatística de líder encontrada para o time {team_id}.")

    except Exception as e:
        print(f"⚠️ Erro ao analisar time {team_id}: {e}")

    while len(top_scorers) < 2:
        top_scorers.append("N/A")

    return {
        "media_3_jogos": media,
        "cestinha_1": top_scorers[0],
        "cestinha_2": top_scorers[1]
    }