# services/style_clash.py
# ==========================================================
# ALERTA DE CHOQUE DE ESTILOS - NBA
# ==========================================================
# Responsável por:
# - Buscar rankings da ESPN
# - Salvar rankings defensivos e ofensivos no PostgreSQL
# - Detectar ALERTA DE CHOQUE DE ESTILOS
# ==========================================================

import requests
import psycopg2
from datetime import date
from psycopg2.extras import execute_batch

# ======================
# ESPN ENDPOINT
# ======================
ESPN_STATS_URL = (
    "https://site.web.api.espn.com/apis/v2/sports/"
    "basketball/nba/statistics/teams"
)

# ======================
# CONFIGURAÇÕES DE RANKING
# ======================
TOP_DEF_LIMIT = 8   # Defesa
TOP_OFF_LIMIT = 5   # Ataque

DEFENSIVE_STATS = {
    "rebounds": "REB",
    "blocks": "BLK",
    "steals": "STL"
}

OFFENSIVE_STATS = {
    "points": "PTS",
    "threePointFieldGoalsMade": "3PM"
}

# ==========================================================
# BUSCAR DADOS DA ESPN
# ==========================================================
def fetch_team_rankings():
    """
    Busca rankings consolidados da NBA na ESPN
    """
    resp = requests.get(ESPN_STATS_URL, timeout=20)
    resp.raise_for_status()
    return resp.json()


# ==========================================================
# EXTRAIR RANKINGS DEFENSIVOS E OFENSIVOS
# ==========================================================
def extract_rankings(data):
    """
    Extrai rankings defensivos (Top 8) e ofensivos (Top 5)
    """
    defensivos = []
    ofensivos = []
    hoje = date.today()

    stats = data.get("results", {}).get("stats", [])

    for stat in stats:
        stat_name = stat.get("name")
        leaders = stat.get("leaders", [])

        # DEFESA
        if stat_name in DEFENSIVE_STATS:
            for pos, team in enumerate(leaders[:TOP_DEF_LIMIT], start=1):
                defensivos.append((
                    int(team["team"]["id"]),
                    team["team"]["displayName"],
                    DEFENSIVE_STATS[stat_name],
                    pos,
                    float(team["value"]),
                    hoje
                ))

        # ATAQUE
        if stat_name in OFFENSIVE_STATS:
            for pos, team in enumerate(leaders[:TOP_OFF_LIMIT], start=1):
                ofensivos.append((
                    int(team["team"]["id"]),
                    team["team"]["displayName"],
                    OFFENSIVE_STATS[stat_name],
                    pos,
                    float(team["value"]),
                    hoje
                ))

    return defensivos, ofensivos


# ==========================================================
# SALVAR RANKINGS NO BANCO
# ==========================================================
def salvar_rankings(defensivos, ofensivos, conn):
    """
    Salva rankings no PostgreSQL (atualização diária)
    """
    with conn.cursor() as cur:

        # Limpeza diária
        cur.execute("""
            DELETE FROM league_defensive_rankings
            WHERE reference_date = CURRENT_DATE
        """)

        cur.execute("""
            DELETE FROM league_offensive_rankings
            WHERE reference_date = CURRENT_DATE
        """)

        # Inserção defensiva
        execute_batch(cur, """
            INSERT INTO league_defensive_rankings
            (team_id, team_name, stat_type, rank_position, stat_value, reference_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, defensivos)

        # Inserção ofensiva
        execute_batch(cur, """
            INSERT INTO league_offensive_rankings
            (team_id, team_name, stat_type, rank_position, stat_value, reference_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ofensivos)

        conn.commit()


# ==========================================================
# ATUALIZAÇÃO DIÁRIA (CHAMADA PELO BOT)
# ==========================================================
def atualizar_rankings_diarios(conn):
    """
    Atualiza rankings defensivos e ofensivos diariamente
    """
    print("🔄 Atualizando rankings NBA (defesa x ataque)...")

    data = fetch_team_rankings()
    defensivos, ofensivos = extract_rankings(data)

    salvar_rankings(defensivos, ofensivos, conn)

    print(
        f"✅ Rankings atualizados | "
        f"Defesa: {len(defensivos)} registros | "
        f"Ataque: {len(ofensivos)} registros"
    )


# ==========================================================
# DETECTAR ALERTA DE CHOQUE DE ESTILOS
# ==========================================================
def verificar_choque_estilos(team_a_id, team_b_id, conn):
    """
    Regra:
    - Time A em pelo menos 1 ranking defensivo
    - Time A em pelo menos 1 ranking ofensivo
    - Time B NÃO pode estar em nenhum ranking
    """

    with conn.cursor() as cur:

        # TIME A
        cur.execute("""
            SELECT 1 FROM league_defensive_rankings
            WHERE team_id = %s AND reference_date = CURRENT_DATE
            LIMIT 1
        """, (team_a_id,))
        a_def = cur.fetchone() is not None

        cur.execute("""
            SELECT 1 FROM league_offensive_rankings
            WHERE team_id = %s AND reference_date = CURRENT_DATE
            LIMIT 1
        """, (team_a_id,))
        a_off = cur.fetchone() is not None

        # TIME B
        cur.execute("""
            SELECT 1 FROM league_defensive_rankings
            WHERE team_id = %s AND reference_date = CURRENT_DATE
            LIMIT 1
        """, (team_b_id,))
        b_def = cur.fetchone() is not None

        cur.execute("""
            SELECT 1 FROM league_offensive_rankings
            WHERE team_id = %s AND reference_date = CURRENT_DATE
            LIMIT 1
        """, (team_b_id,))
        b_off = cur.fetchone() is not None

    if a_def and a_off and not (b_def or b_off):
        print("🚨 ALERTA DE CHOQUE DE ESTILOS DETECTADO")
        return True, "🚨 ALERTA DE CHOQUE DE ESTILOS"

    return False, None
