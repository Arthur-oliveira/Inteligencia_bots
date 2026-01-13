from database.database_manager import log, buscar_dados
from endpoints.api_handler import get_team_schedule

def verificar_presenca_nos_tops(team_name):
    """Verifica rankings defensivos (Top 8) e ofensivos (Top 5)."""
    sql_def = "SELECT COUNT(*) as total FROM league_defensive_rankings WHERE team = %s AND rank_position <= 8"
    res_def = buscar_dados(sql_def, (team_name,))
    tem_defesa = res_def[0]['total'] > 0 if res_def else False

    sql_off = "SELECT COUNT(*) as total FROM league_offensive_rankings WHERE team = %s AND rank_position <= 5"
    res_off = buscar_dados(sql_off, (team_name,))
    tem_ataque = res_off[0]['total'] > 0 if res_off else False

    return tem_defesa, tem_ataque

def analisar_confronto_estilos(time_a_nome, time_b_nome):
    """Lógica do Choque de Estilos."""
    a_def, a_atk = verificar_presenca_nos_tops(time_a_nome)
    b_def, b_atk = verificar_presenca_nos_tops(time_b_nome)

    if (a_def and a_atk) and not (b_def or b_atk):
        return True, time_a_nome
    if (b_def and b_atk) and not (a_def or a_atk):
        return True, time_b_nome

    return False, None

def calcular_media_pontos_equipe(team_id):
    """Busca últimos 3 placares e retorna a média."""
    eventos = get_team_schedule(team_id)
    placares = []

    for event in eventos:
        if event.get('status', {}).get('type', {}).get('completed'):
            competicoes = event.get('competitions', [])
            for competitor in competicoes[0].get('competitors', []):
                if str(competitor.get('team', {}).get('id')) == str(team_id):
                    score = competitor.get('score', {}).get('value')
                    if score: placares.append(int(score))

    ultimos_3 = placares[-3:] if len(placares) >= 3 else placares
    return sum(ultimos_3) / len(ultimos_3) if ultimos_3 else 0.0