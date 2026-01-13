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

def gerar_agenda_simplificada(jogos):
    """
    Gera o 1º Envio: Agenda formatada.
    """
    texto = "📅 <b>AGENDA NBA DE HOJE</b>\n\n"
    
    for j in jogos:
        # Formatação: 🕒 20:00 - TimeA x TimeB
        confronto = f"<b>{j['nome_casa']}</b> x <b>{j['nome_fora']}</b>"
        texto += f"🕒 20:00 - {confronto}\n"
    
    texto += "\n🤖 A análise detalhada será enviada!"
    return texto

def gerar_status_news(jogos):
    """
    Gera o Status News com espaçamento duplo e especificando o quesito do TOP Player.
    """
    texto = "📊 <b>Status News :</b>\n\n"
    tem_conteudo = False 
    
    for j in jogos:
        times_para_analisar = [
            {'id': j['id_casa'], 'nome': j['nome_casa']},
            {'id': j['id_fora'], 'nome': j['nome_fora']}
        ]

        for time in times_para_analisar:
            # 1. Lesão
            lesao = buscar_dados(
                "SELECT player_name FROM team_top_scorers WHERE team_id = %s AND is_injured = TRUE LIMIT 1", 
                (str(time['id']),)
            )
            # 2. Ofensivo
            mvp_off = buscar_dados(
                "SELECT player_name, rank_position FROM league_offensive_rankings WHERE team = %s AND rank_position <= 5 LIMIT 1", 
                (time['nome'],)
            )
            # 3. Defensivo
            mvp_def = buscar_dados(
                "SELECT player_name, rank_position FROM league_defensive_rankings WHERE team = %s AND rank_position <= 5 LIMIT 1", 
                (time['nome'],)
            )

            if not lesao and not mvp_off and not mvp_def:
                continue

            prompt = ""
            if lesao:
                jogador = lesao[0]['player_name']
                prompt = (f"O jogador {jogador} do time {time['nome']} está lesionado. "
                          f"Escreva uma frase jornalística curta (max 15 palavras) sobre esse desfalque.")
            elif mvp_off:
                jogador = mvp_off[0]['player_name']
                posicao = mvp_off[0]['rank_position']
                prompt = (f"O jogador {jogador} do time {time['nome']} é Top {posicao} em PONTUAÇÃO. "
                          f"Escreva uma frase curta (max 15 palavras) destacando essa liderança.")
            elif mvp_def:
                jogador = mvp_def[0]['player_name']
                posicao = mvp_def[0]['rank_position']
                prompt = (f"O jogador {jogador} do time {time['nome']} é Top {posicao} em DEFESA. "
                          f"Escreva uma frase curta (max 15 palavras) destacando essa dominância.")

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
    """
    m_casa = calcular_media_pontos_equipe(partida['id_casa'])
    m_fora = calcular_media_pontos_equipe(partida['id_fora'])
    
    atleta_casa = buscar_dados("SELECT player_name, last_3_avg FROM team_top_scorers WHERE team_id = %s AND is_injured = FALSE LIMIT 1", (str(partida['id_casa']),))
    atleta_fora = buscar_dados("SELECT player_name, last_3_avg FROM team_top_scorers WHERE team_id = %s AND is_injured = FALSE LIMIT 1", (str(partida['id_fora']),))

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
    Alerta de Choque de Estilos com Estratégia MÚLTIPLA.
    (Separadores === removidos)
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

    # 2.3 Jogador Ofensivo (Top Scorer)
    off_data = buscar_dados("SELECT player_name, avg_points FROM league_offensive_rankings WHERE team = %s ORDER BY rank_position ASC LIMIT 1", (time_vant,))
    if off_data:
        pts = calcular_palpite_par(off_data[0]['avg_points'])
        multipla.append(f"✔️ {off_data[0]['player_name']} {pts}+ pontos")

    # 2.4 Jogador Defensivo (Top Defensive) -> Regra: Tentar oferecer pontos
    def_data = buscar_dados("SELECT player_name, avg_steals, avg_blocks FROM league_defensive_rankings WHERE team = %s ORDER BY rank_position ASC LIMIT 1", (time_vant,))
    if def_data:
        p_name = def_data[0]['player_name']
        
        # Tenta buscar a média de pontos desse jogador defensivo
        p_off_stats = buscar_dados("SELECT avg_points FROM league_offensive_rankings WHERE player_name = %s", (p_name,))
        
        if p_off_stats:
            # Se achou pontos, usa pontos (conforme regra)
            pts_def = calcular_palpite_par(p_off_stats[0]['avg_points'])
            multipla.append(f"✔️ {p_name} {pts_def}+ pontos")
        else:
            # Fallback: Se não achou pontos, usa a estatística defensiva (Toco/Roubo)
            stl = float(def_data[0]['avg_steals'])
            blk = float(def_data[0]['avg_blocks'])
            
            if stl >= 0.7:
                val = 1 if stl >= 1.3 else 0.5 
                line_type = "roubo" if val == 0.5 else "roubos"
                multipla.append(f"✔️ {p_name} {val}+ {line_type}")
            elif blk >= 0.7:
                val = 1 if blk >= 1.3 else 0.5
                line_type = "toco" if val == 0.5 else "tocos"
                multipla.append(f"✔️ {p_name} {val}+ {line_type}")

    # Montagem das linhas da múltipla
    lines_multipla = "\n".join(multipla)

    # Retorno SEM OS SEPARADORES ===
    return (f"🚨 <b>ALERTA DE CHOQUE DE ESTILOS</b> 🚨\n"
            f"(Diferença defensiva e ofensiva)\n\n"
            f"{texto_ia}\n\n"
            f"🏀💰 <b>MÚLTIPLA:</b>\n\n"
            f"{lines_multipla}\n\n"
            f"ℹ️ <b>Nota Técnica:</b>\n"
            f"Cenários como ajustes de rotação podem reduzir minutos de titulares, impactando mercados individuais fiquem atentos aos jogos.")