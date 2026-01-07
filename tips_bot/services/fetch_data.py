import os
import requests
import psycopg2
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "dbname": os.getenv("DB_NAME"),
    "port": os.getenv("DB_PORT"),
}

# ======================
# CONEXÃO BANCO
# ======================
def get_conn():
    return psycopg2.connect(**DB_CONFIG)


# ======================
# JOGOS DO DIA (FUTUROS)
# ======================
def buscar_jogos_dia():
    hoje = datetime.now().strftime("%Y%m%d")
    resp = requests.get(f"{BASE}/scoreboard?dates={hoje}", timeout=15)
    data = resp.json()

    jogos = []
    for ev in data.get("events", []):
        comp = ev["competitions"][0]
        jogos.append({
            "game_id": ev["id"],
            "data": ev["date"],
            "mandante": comp["competitors"][0],
            "visitante": comp["competitors"][1],
        })

    return jogos


# ======================
# ÚLTIMOS JOGOS FINALIZADOS
# ======================
def buscar_ultimos_jogos(team_id, limite=3):
    hoje = datetime.now()
    encontrados = []

    for i in range(1, 15):
        data = (hoje - timedelta(days=i)).strftime("%Y%m%d")
        resp = requests.get(f"{BASE}/scoreboard?dates={data}", timeout=15)

        if resp.status_code != 200:
            continue

        data_json = resp.json()

        for ev in data_json.get("events", []):
            comp = ev["competitions"][0]

            if not comp["status"]["type"]["completed"]:
                continue

            for c in comp["competitors"]:
                if c["team"]["id"] == team_id:
                    encontrados.append(ev)
                    break

        if len(encontrados) >= limite:
            break

    return encontrados[:limite]


# ======================
# MÉDIA DE PONTOS (TIME)
# ======================
def media_ultimos_3_jogos(team_id):
    jogos = buscar_ultimos_jogos(team_id, 3)
    pontos = []

    for ev in jogos:
        comp = ev["competitions"][0]
        for c in comp["competitors"]:
            if c["team"]["id"] == team_id:
                pontos.append(int(c["score"]))

    if not pontos:
        return 0.0

    return round(sum(pontos) / len(pontos), 1)


# ======================
# CESTINHA DO TIME (ÚLTIMOS 3 JOGOS)
# ======================
def buscar_cestinha(team_id):
    jogos = buscar_ultimos_jogos(team_id, 3)
    acumulado = defaultdict(list)

    for ev in jogos:
        game_id = ev["id"]
        resp = requests.get(f"{BASE}/summary?event={game_id}", timeout=15)

        if resp.status_code != 200:
            continue

        box = resp.json()
        players = box.get("boxscore", {}).get("players", [])

        for team in players:
            if team["team"]["id"] != team_id:
                continue

            stats_block = team["statistics"][0]
            labels = stats_block["labels"]

            # Descobre dinamicamente o índice de PTS
            if "PTS" not in labels:
                continue

            idx_pts = labels.index("PTS")

            for atleta in stats_block["athletes"]:
                stats = atleta["stats"]

                if idx_pts >= len(stats):
                    continue

                pts = stats[idx_pts]
                if pts.isdigit():
                    acumulado[atleta["athlete"]["displayName"]].append(int(pts))

    if not acumulado:
        return None, 0.0

    medias = {}
    for nome, lista in acumulado.items():
        if len(lista) >= 2:
            medias[nome] = sum(lista) / len(lista)

    if not medias:
        return None, 0.0

    cestinha = max(medias, key=medias.get)
    return cestinha, round(medias[cestinha], 1)


# ======================
# SALVAR CESTINHA
# ======================
def salvar_cestinha(team_id, team_name, jogador, media):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO team_top_scorers (
            team_id,
            team_name,
            player_name,
            avg_points,
            games_used,
            last_game
        )
        VALUES (%s, %s, %s, %s, 3, now())
        ON CONFLICT (team_id, player_name)
        DO UPDATE SET
            avg_points = EXCLUDED.avg_points,
            last_game = now()
    """, (team_id, team_name, jogador, media))

    conn.commit()
    cur.close()
    conn.close()
