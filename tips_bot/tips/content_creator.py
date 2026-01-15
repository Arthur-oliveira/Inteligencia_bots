import google.generativeai as genai
import os
from database.database_manager import log, calcular_palpite_par, buscar_dados
from tips.strategy_processor import calcular_media_pontos_equipe

# IA Configurada (Temperatura 0.4 para precisão)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model_name = "gemini-2.0-flash"
model = genai.GenerativeModel(
    model_name=model_name, 
    generation_config={"temperature": 0.4}
)

log.info(f"🧠 Modelo de IA carregado: {model_name} (Temp 0.4)")

# --- FUNÇÃO HELPER DE SEGURANÇA (BLACKLIST) ---
def is_player_injured_blacklist(player_name):
    """
    Verifica se o jogador está na tabela 'injuries'.
    Retorna True se estiver machucado/bloqueado.
    """
    if not player_name: 
        return False
        
    # Verifica pelo NOME (Compatibilidade e Segurança)
    # Usamos ILIKE para ignorar maiúsculas/minúsculas
    res = buscar_dados("SELECT 1 FROM injuries WHERE player_name ILIKE %s LIMIT 1", (player_name.strip(),))
    return True if res else False
# -----------------------------------------------

def gerar_agenda_simplificada(jogos):
    """
    Gera o 1º Envio: Agenda formatada.
    """
    texto = "📅 <b>AGENDA NBA DE HOJE</b>\n\n"
    
    for j in jogos:
        confronto = f"<b>{j['nome_casa']}</b> x <b>{j['nome_fora']}</b>"
        texto += f"🕒 {j['horario']} - {confronto}\n"
    
    texto += "\n🤖 A análise detalhada será enviada!"
    return texto

def gerar_status_news(jogos):
    """
    Gera o Status News.
    Detecta se o MVP está na Blacklist de Injuries e reporta como desfalque.
    """
    texto = "📊 <b>Status News :</b>\n\n"
    tem_conteudo = False 
    
    for j in jogos:
        times_para_analisar = [
            {'id': j['id_casa'], 'nome': j['nome_casa']},
            {'id': j['id_fora'], 'nome': j['nome_fora']}
        ]

        for time in times_para_analisar:
            # 1. Busca Ofensivo (Top Ranking)
            mvp_off = buscar_dados(
                "SELECT player_name, rank_position FROM league_offensive_rankings WHERE team = %s AND rank_position <= 5 LIMIT 1", 
                (time['nome'],)
            )
            
            prompt = ""
            
            if mvp_off:
                jogador = mvp_off[0]['player_name']
                posicao = mvp_off[0]['rank_position']
                
                # VERIFICAÇÃO DE LESÃO (BLACKLIST)
                if is_player_injured_blacklist(jogador):
                    # O jogador é Craque, mas está OFF.
                    prompt = (f"O craque {jogador} do time {time['nome']} (Top {posicao} da liga) está MACHUCADO e fora do jogo. "
                              f"Escreva uma frase jornalística curta (max 15 palavras) sobre o impacto desse desfalque.")
                else:
                    # Jogador saudável
                    prompt = (f"O jogador {jogador} do time {time['nome']} é Top {posicao} em PONTUAÇÃO. "
                              f"Escreva uma frase curta (max 15 palavras) destacando essa liderança.")
            
            # Se não achou MVP ofensivo ou não gerou prompt, tenta Defensivo
            elif not prompt: 
                mvp_def = buscar_dados(
                    "SELECT player_name, rank_position FROM league_defensive_rankings WHERE team = %s AND rank_position <= 5 LIMIT 1", 
                    (time['nome'],)
                )
                if mvp_def:
                    jogador = mvp_def[0]['player_name']
                    posicao = mvp_def[0]['rank_position']
                    
                    if is_player_injured_blacklist(jogador):
                         prompt = (f"O defensor de elite {jogador} do time {time['nome']} está MACHUCADO. "
                                   f"Escreva uma frase curta sobre o desfalque defensivo.")
                    else:
                        prompt = (f"O jogador {jogador} do time {time['nome']} é Top {posicao} em DEFESA. "
                                  f"Escreva uma frase curta destacando essa dominância.")

            if not prompt:
                continue

            try:
                analise_ia = model.generate_content(prompt).text.strip().replace(f"{time['nome']}:", "").strip()
                texto += f"<b>{time['nome']}</b>: {analise_ia}\n\n"
                tem_conteudo = True
            except Exception as e:
                log.error(f"Erro IA Status News {time['nome']}: {e}")
                continue

    if not tem_conteudo:
        texto += "Nenhum destaque estatístico crítico para a rodada de hoje.\n"

    return texto

def preparar_bilhete_free(partida):
    """
    Gera o Bilhete Free completo.
    Filtra jogadores lesionados das sugestões.
    """
    m_casa = calcular_media_pontos_equipe(partida['id_casa'])
    m_fora = calcular_media_pontos_equipe(partida['id_fora'])
    
    # Busca atletas candidatos
    atleta_casa_cand = buscar_dados("SELECT player_name, last_3_avg FROM team_top_scorers WHERE team_id = %s LIMIT 1", (str(partida['id_casa']),))
    atleta_fora_cand = buscar_dados("SELECT player_name, last_3_avg FROM team_top_scorers WHERE team_id = %s LIMIT 1", (str(partida['id_fora']),))

    # Validação via Blacklist Injuries
    atleta_casa = None
    if atleta_casa_cand and not is_player_injured_blacklist(atleta_casa_cand[0]['player_name']):
        atleta_casa = atleta_casa_cand
        
    atleta_fora = None
    if atleta_fora_cand and not is_player_injured_blacklist(atleta_fora_cand[0]['player_name']):
        atleta_fora = atleta_fora_cand

    prompt = (f"Escreva uma análise curta (máximo 25 palavras) e vibrante sobre o jogo {partida['nome_casa']} x {partida['nome_fora']}. "
              f"Foque na expectativa de pontos e rivalidade. Use tom de narrador.")
    analise = model.generate_content(prompt).text.strip()

    texto_base = f"🏀 <b>Bilhete Free</b>\n\n"
    texto_base += f"🏀 <b>{partida['nome_casa']}</b> x <b>{partida['nome_fora']}</b>\n\n"
    texto_base += f"📊 <b>CONFRONTO</b>\n\n"
    texto_base += f"🏀🔥 {analise}\n\n"
    
    texto_destaques = "⭐️ <b>DESTAQUES</b>\n\n"
    tem_destaque = False
    
    if atleta_casa:
        texto_destaques += f"🔥 {atleta_casa[0]['player_name']} (<b>{partida['nome_casa']}</b>)\n"
        tem_destaque = True
    if atleta_fora:
        texto_destaques += f"🔥 {atleta_fora[0]['player_name']} (<b>{partida['nome_fora']}</b>)\n"
        tem_destaque = True
    
    texto_destaques += "\n"

    entradas_validas = []

    if m_casa >= 105:
        entradas_validas.append(f"🏀 <b>{partida['nome_casa']}</b> {calcular_palpite_par(m_casa)}+ pontos")
    if m_fora >= 105:
        entradas_validas.append(f"🏀 <b>{partida['nome_fora']}</b> {calcular_palpite_par(m_fora)}+ pontos")

    if atleta_casa:
        entradas_validas.append(f"👤 {atleta_casa[0]['player_name']} {calcular_palpite_par(atleta_casa[0]['last_3_avg'])}+ pontos")
    if atleta_fora:
        entradas_validas.append(f"👤 {atleta_fora[0]['player_name']} {calcular_palpite_par(atleta_fora[0]['last_3_avg'])}+ pontos")

    if not entradas_validas:
        return None

    texto_final = texto_base
    if tem_destaque:
        texto_final += texto_destaques
    
    texto_final += "🔥 <b>POSSÍVEIS ENTRADAS</b>\n\n"
    for entrada in entradas_validas:
        texto_final += f"{entrada}\n"
    
    return texto_final

def gerar_choque_formatado(time_vant, time_rival):
    """
    Alerta de Choque de Estilos com Múltipla.
    Bloqueia jogadores da Blacklist 'injuries'.
    """
    # 1. Geração do Texto de Alerta (IA)
    prompt = (
        f"O time {time_vant} tem uma vantagem estatística muito forte (choque de estilos) contra o {time_rival}. "
        f"Escreva um alerta de 2 frases curtas e sérias destacando essa superioridade e desequilíbrio. "
        f"Comece com 'O {time_vant} entra em quadra...' ou similar. Seja profissional."
    )
    texto_ia = model.generate_content(prompt).text.strip()
    
    # 2. Busca de Dados para a MÚLTIPLA
    multipla = []
    
    # 2.1 Vitória Simples
    multipla.append(f"✔️ Vitória <b>{time_vant}</b>")
    
    # 2.2 Team Over 110+ (Time Dominante)
    multipla.append(f"✔️ <b>{time_vant}</b> 110+ pontos")

    # --- LÓGICA DE SELEÇÃO DE JOGADORES (ATAQUE) ---
    selected_off_player = None

    off_candidates = buscar_dados("SELECT player_name, avg_points FROM league_offensive_rankings WHERE team = %s ORDER BY rank_position ASC LIMIT 10", (time_vant,))
    
    for cand in off_candidates:
        nome_cand = cand['player_name']
        
        # VERIFICAÇÃO NA BLACKLIST (INJURIES)
        if is_player_injured_blacklist(nome_cand):
            continue 
            
        # Apto
        pts = calcular_palpite_par(cand['avg_points'])
        multipla.append(f"✔️ {nome_cand} {pts}+ pontos")
        selected_off_player = nome_cand 
        break 

    # --- LÓGICA DE SELEÇÃO DE JOGADORES (DEFESA) ---
    def_candidates = buscar_dados("SELECT player_name, avg_steals, avg_blocks FROM league_defensive_rankings WHERE team = %s ORDER BY rank_position ASC LIMIT 10", (time_vant,))
    
    for cand in def_candidates:
        p_name = cand['player_name']
        
        # CRITÉRIO 1: Evita Duplicidade 
        if selected_off_player and p_name.lower().strip() == selected_off_player.lower().strip():
            continue
            
        # CRITÉRIO 2: VERIFICAÇÃO NA BLACKLIST (INJURIES)
        if is_player_injured_blacklist(p_name):
            continue 

        # Apto e Único
        p_off_stats = buscar_dados("SELECT avg_points FROM league_offensive_rankings WHERE player_name ILIKE %s", (p_name,))
        
        if p_off_stats:
            pts_def = calcular_palpite_par(p_off_stats[0]['avg_points'])
            multipla.append(f"✔️ {p_name} {pts_def}+ pontos")
        else:
            stl = float(cand['avg_steals'])
            blk = float(cand['avg_blocks'])
            
            if stl >= 0.7:
                val = 1 if stl >= 1.3 else 0.5 
                line_type = "roubo" if val == 0.5 else "roubos"
                multipla.append(f"✔️ {p_name} {val}+ {line_type}")
            elif blk >= 0.7:
                val = 1 if blk >= 1.3 else 0.5
                line_type = "toco" if val == 0.5 else "tocos"
                multipla.append(f"✔️ {p_name} {val}+ {line_type}")
        
        break

    lines_multipla = "\n".join(multipla)

    return (f"🚨 <b>ALERTA DE CHOQUE DE ESTILOS</b> 🚨\n"
            f"(Diferença defensiva e ofensiva)\n\n"
            f"{texto_ia}\n\n"
            f"🏀💰 <b>MÚLTIPLA:</b>\n\n"
            f"{lines_multipla}\n\n"
            f"ℹ️ <b>Nota Técnica:</b>\n"
            f"Cenários como ajustes de rotação podem reduzir minutos de titulares, impactando mercados individuais fiquem atentos aos jogos.")