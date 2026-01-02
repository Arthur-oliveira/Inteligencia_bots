# C:\inteligencia_bots\tips_bot\services\notifier_telegram.py
import requests
import math
import os
from dotenv import dotenv_values

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
config = dotenv_values(env_path)
TOKEN = config.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = config.get("TELEGRAM_CHAT_ID")

def calcular_linha_jogador(ppg):
    if ppg < 10: return "10+"
    linha = math.floor(ppg / 5) * 5
    return f"{linha}+"

def get_sobrenome(nome_completo):
    if not nome_completo or nome_completo == "N/A": return ""
    return nome_completo.split()[-1]

def get_nome_curto_time(nome_time):
    if not nome_time: return ""
    return nome_time.split()[-1]

def enviar_lista_agenda(jogos):
    if not TOKEN or not CHAT_ID: return
    msg = "📅 **AGENDA NBA DE HOJE**\n\n"
    for jogo in jogos:
        hora = jogo.get('hora', '--:--')
        m = get_nome_curto_time(jogo['mandante_nome'])
        v = get_nome_curto_time(jogo['visitante_nome'])
        msg += f"🕒 {hora} - {v} x {m}\n"
    msg += "\n🤖 *A análise detalhada será enviada em breve!*"
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def formatar_bilhete(dados):
    m_nome_curto = get_nome_curto_time(dados['principal'])
    v_nome_curto = get_nome_curto_time(dados['visitor'])

    msg = f"🏀 {dados['visitor']} x {dados['principal']}\n\n"
    
    msg += "📊 CONFRONTO\n\n"
    msg += f"🏀🔥 {dados.get('confronto_analise', '').strip()}\n\n"
    
    msg += "⭐️ DESTAQUES\n\n"
    if dados['m_basket'] != "N/A":
        msg += f"🔥 {dados['m_basket']} ({dados.get('m_comentario', '')})\n"
    if dados['v_basket'] != "N/A":
        msg += f"🔥 {dados['v_basket']} ({dados.get('v_comentario', '')})\n"
    
    msg += "--------------------------------------------------------------------\n"
    msg += "🔥 POSSÍVEIS ENTRADAS\n\n"
    
    if dados['v_media_3'] > 100:
        msg += f"🏀 {v_nome_curto} 110+ pontos\n"
    if dados['m_media_3'] > 100:
        msg += f"🏀 {m_nome_curto} 110+ pontos\n"
        
    if dados['v_final_nome'] != "N/A":
        msg += f"👤 {get_sobrenome(dados['v_final_nome'])} {calcular_linha_jogador(dados['v_final_ppg'])} pontos\n"
    if dados['m_final_nome'] != "N/A":
        msg += f"👤 {get_sobrenome(dados['m_final_nome'])} {calcular_linha_jogador(dados['m_final_ppg'])} pontos\n"

    return msg

def enviar_telegram(dados_jogo):
    if not TOKEN or not CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": formatar_bilhete(dados_jogo)})
    except: pass