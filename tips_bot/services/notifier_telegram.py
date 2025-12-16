# C:\inteligencia_bots\tips_bot\services\notifier_telegram.py
import requests
import math
from dotenv import dotenv_values

config = dotenv_values(".env")
TOKEN = config.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = config.get("TELEGRAM_CHAT_ID")

def calcular_linha_jogador(ppg):
    """
    Arredonda para baixo para o múltiplo de 5 mais próximo.
    Ex: 32.5 -> 30+ | 28.9 -> 25+ | 14.0 -> 10+
    """
    if ppg < 10: return "10+"
    linha = math.floor(ppg / 5) * 5
    return f"{linha}+"

def get_sobrenome(nome_completo):
    if not nome_completo: return ""
    return nome_completo.split()[-1]

def get_nome_curto_time(nome_time):
    if not nome_time: return ""
    return nome_time.split()[-1]

def formatar_bilhete(dados):
    m_nome = dados['principal']
    v_nome = dados['visitor']
    m_nome_curto = get_nome_curto_time(m_nome)
    v_nome_curto = get_nome_curto_time(v_nome)

    # 1. CABEÇALHO
    msg = f"🏀 {v_nome} x {m_nome}\n\n"
    
    # 2. CONFRONTO
    msg += "📊 CONFRONTO\n\n" # Adicionado espaçamento extra
    
    analise_ia = dados.get('confronto_analise')
    if analise_ia:
        # Tenta melhorar o espaçamento entre os tópicos da IA para não ficarem colados
        # Troca quebras simples por duplas para dar o ar que você pediu
        texto_formatado = analise_ia.replace("\n", "\n\n")
        msg += texto_formatado + "\n"
    else:
        msg += "• Aguardando análise detalhada...\n"

    msg += "\n"
    
    # 3. DESTAQUES
    msg += "⭐ DESTAQUES\n\n" # Adicionado espaçamento extra
    
    m_basket = dados['m_basket']
    if m_basket and m_basket != "N/A":
        msg += f"🔥 {m_basket} ({m_nome_curto})\n"
    
    v_basket = dados['v_basket']
    if v_basket and v_basket != "N/A":
        msg += f"🔥 {v_basket} ({v_nome_curto})\n"
    
    msg += "\n" + "-"*36 + "\n\n"
    
    # 4. POSSÍVEIS ENTRADAS
    msg += "🔥 POSSÍVEIS ENTRADAS\n\n" # Adicionado espaçamento extra
    
    # --- BLOCO DE TIMES ---
    tem_times = False
    if dados['v_media_3'] > 100:
        msg += f"🏀 {v_nome_curto} 110+ pontos\n"
        tem_times = True
    if dados['m_media_3'] > 100:
        msg += f"🏀 {m_nome_curto} 110+ pontos\n"
        tem_times = True
    
    # Adiciona espaço entre Times e Jogadores se houver times listados
    if tem_times:
        msg += "\n"
    
    # --- BLOCO DE JOGADORES ---
    # Visitante
    v_ppg = dados.get('v_basket_ppg', 0)
    v_status = dados.get('v_status', '')
    if v_basket and v_basket != "N/A":
        if "out" not in str(v_status).lower():
            msg += f"👤 {get_sobrenome(v_basket)} {calcular_linha_jogador(v_ppg)} pontos\n"
        else:
            v_reserv = dados.get('v_reserv')
            v_reserv_ppg = dados.get('v_reserv_ppg', 0)
            if v_reserv:
                msg += f"👤 {get_sobrenome(v_reserv)} {calcular_linha_jogador(v_reserv_ppg)} pontos\n"

    # Mandante
    m_ppg = dados.get('m_basket_ppg', 0)
    m_status = dados.get('m_status', '')
    if m_basket and m_basket != "N/A":
        if "out" not in str(m_status).lower():
            msg += f"👤 {get_sobrenome(m_basket)} {calcular_linha_jogador(m_ppg)} pontos\n"
        else:
            m_reserv = dados.get('m_reserv')
            m_reserv_ppg = dados.get('m_reserv_ppg', 0)
            if m_reserv:
                msg += f"👤 {get_sobrenome(m_reserv)} {calcular_linha_jogador(m_reserv_ppg)} pontos\n"

    return msg

def enviar_telegram(dados_jogo):
    if not TOKEN or not CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": formatar_bilhete(dados_jogo)})
        print("✅ Bilhete enviado.")
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")