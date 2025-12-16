# services/strategy_handicap.py

from datetime import date
from services.utils import normalizar_nome_time

def calcular_margem_projetada(m_stats, v_stats, b2b_m, b2b_v):
    """
    Calcula a margem de vitória esperada do MANDANTE baseada em eficiência.
    """
    # 1. Diferença de Net Rating (A métrica mais importante)
    diff_net_rating = m_stats['NET_RATING'] - v_stats['NET_RATING']
    
    # 2. Ajuste de Pace (Ritmo)
    media_pace = (m_stats['PACE'] + v_stats['PACE']) / 2
    fator_pace = media_pace / 100.0
    
    margem_base = diff_net_rating * fator_pace
    
    # 3. Vantagem de Casa (Home Court)
    home_court = 2.5
    
    # 4. Penalidade de Cansaço (Back-to-Back)
    penalidade_b2b = 2.0
    
    ajuste_cansaco = 0
    if b2b_m: ajuste_cansaco -= penalidade_b2b
    if b2b_v: ajuste_cansaco += penalidade_b2b
    
    return margem_base + home_court + ajuste_cansaco

def extrair_linha_handicap(spread_str, mandante_nome):
    """
    Transforma string de handicap em float referente ao MANDANTE.
    """
    try:
        # Trata casos de 'Even', 'null' ou vazio
        if not spread_str or str(spread_str).lower() in ["even", "none", "null"]:
            return 0.0
            
        parts = spread_str.split(' ')
        if len(parts) < 2:
            return 0.0
            
        valor = float(parts[-1])
        
        # Se a sigla (ex: LAL) está no nome do mandante, o valor é dele.
        # Caso contrário, inverte o sinal.
        if parts[0][:3].upper() in mandante_nome.upper():
            return valor
        else:
            return -valor
    except:
        return 0.0

def gerar_payload_handicap(jogo, nba_stats_dict):
    """
    Gera a análise completa cruzando ESPN (jogo) e NBA API (stats).
    """
    mandante = jogo.get("mandante")
    visitante = jogo.get("visitante")
    spread_str = jogo.get("handicap_linha")
    
    # --- CORREÇÃO DE NOMES ---
    nome_m_nba = normalizar_nome_time(mandante)
    nome_v_nba = normalizar_nome_time(visitante)
    
    # Recupera stats (padrao zerado se falhar)
    padrao = {'NET_RATING': 0.0, 'PACE': 100.0}
    
    # Busca stats do mandante
    if nome_m_nba in nba_stats_dict:
        m_stats = nba_stats_dict[nome_m_nba]
    else:
        # Tentativa de busca aproximada (contém string)
        m_stats = next((v for k, v in nba_stats_dict.items() if mandante in k), padrao)

    # Busca stats do visitante
    if nome_v_nba in nba_stats_dict:
        v_stats = nba_stats_dict[nome_v_nba]
    else:
        v_stats = next((v for k, v in nba_stats_dict.items() if visitante in k), padrao)
    
    # Aviso no terminal se os dados estiverem zerados (ajuda a debugar nomes errados)
    if m_stats['NET_RATING'] == 0.0 and v_stats['NET_RATING'] == 0.0:
        print(f"⚠️ AVISO: Stats não encontradas para {mandante} ou {visitante}. Verifique 'services/utils.py'.")

    # --- CÁLCULOS ---
    is_b2b_m = False # Futuramente integrar verificação real
    is_b2b_v = False
    
    margem_justa = calcular_margem_projetada(m_stats, v_stats, is_b2b_m, is_b2b_v)
    linha_mercado = extrair_linha_handicap(spread_str, mandante)
    
    # Edge = Margem Justa + Linha Mercado
    edge = margem_justa + linha_mercado 
    
    # Probabilidade (Modelo Linear: 0 edge = 50%, 1 ponto edge = +3%)
    hp_prob = 50.0 + (edge * 3.0)
    hp_prob = max(1.0, min(99.0, hp_prob))
    
    # Tendência
    trend = "equilibrado"
    if hp_prob >= 55:
        trend = "mandante"
    elif hp_prob <= 45:
        trend = "visitante"
        hp_prob = 100.0 - hp_prob # Inverte para mostrar a chance do visitante
    
    # Risco
    if hp_prob >= 60: hp_risk = "BAIXO"
    elif hp_prob >= 53: hp_risk = "MÉDIO"
    else: hp_risk = "ALTO"
    
    hp_conf = int(hp_prob)

    # Justificativa técnica (fica salva no banco, mas não vai pro telegram poluída)
    justification = (
        f"NetRtg: {m_stats['NET_RATING']} vs {v_stats['NET_RATING']}. "
        f"Projeção: {margem_justa:.1f}. Linha: {linha_mercado}. "
        f"Edge: {abs(edge):.1f}."
    )

    payload = {
        "dt_report": date.today(),
        "num_games": 1,
        "context": "NBA Analytics",
        "game_id": jogo.get("jogo_id"),
        "league": jogo.get("liga"),
        "principal": mandante,
        "visitor": visitante,
        "game_datetime": jogo.get("data_jogo"),
        "hp_lines": spread_str if spread_str else "0.0",
        "hp_prob": round(hp_prob, 2),
        "hp_risk": hp_risk,
        "hp_conf": hp_conf,
        "justification": justification,
        "trend": trend,
        # Dados extras para filtrar mensagens vazias no telegram
        "m_net_rtg": m_stats['NET_RATING'],
        "v_net_rtg": v_stats['NET_RATING']
    }

    return payload