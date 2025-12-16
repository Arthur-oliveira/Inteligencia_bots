# services/notifier_telegram.py
import requests
from dotenv import dotenv_values

config = dotenv_values(".env")

# Apenas carrega do arquivo. Se não existir, será None.
TOKEN = config.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = config.get("TELEGRAM_CHAT_ID")

def formatar_bilhete(dados_jogo):
    m_nome = dados_jogo['principal']
    v_nome = dados_jogo['visitor']
    
    msg = f"🚨 **Atenção** ao seguinte jogo de hoje:\n\n"
    msg += f"🏀 **{v_nome} X {m_nome}**\n\n"
    
    motivos = []
    if dados_jogo['m_media_3'] > 100:
        motivos.append(f"Nos últimos jogos a média do **{m_nome}** foi superior a 100 pontos ({dados_jogo['m_media_3']:.1f}).")
    if dados_jogo['v_media_3'] > 100:
        motivos.append(f"Nos últimos jogos a média do **{v_nome}** foi superior a 100 pontos ({dados_jogo['v_media_3']:.1f}).")
    
    msg += "\n".join(motivos) + "\n\n"
    msg += "E os principais pontuadores têm marcado presença:\n\n"
    
    # Visitante
    v_basket = dados_jogo['v_basket']
    v_status = dados_jogo['v_status']
    v_reserv = dados_jogo['v_reserv']
    
    msg += f"👤 **Principal Pontuador {v_nome}:**\n"
    if v_status and "out" in str(v_status).lower():
        msg += f"⚠️ {v_basket} está **FORA** ({v_status}).\n"
        msg += f"👀 Fique de olho em: **{v_reserv}** (2º maior pontuador)."
    else:
        status_txt = "✅ Jogando" if not v_status or v_status == "Active" else f"⚠️ {v_status}"
        msg += f"🔥 **{v_basket}** ({status_txt})"
    
    msg += "\n\n"

    # Mandante
    m_basket = dados_jogo['m_basket']
    m_status = dados_jogo['m_status']
    m_reserv = dados_jogo['m_reserv']
    
    msg += f"👤 **Principal Pontuador {m_nome}:**\n"
    if m_status and "out" in str(m_status).lower():
        msg += f"⚠️ {m_basket} está **FORA** ({m_status}).\n"
        msg += f"👀 Fique de olho em: **{m_reserv}** (2º maior pontuador)."
    else:
        status_txt = "✅ Jogando" if not m_status or m_status == "Active" else f"⚠️ {m_status}"
        msg += f"🔥 **{m_basket}** ({status_txt})"

    return msg

def enviar_telegram(dados_jogo):
    if not TOKEN or not CHAT_ID:
        print("❌ ERRO: Token ou Chat ID não encontrados no .env!")
        return

    mensagem = formatar_bilhete(dados_jogo)
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(url, json=payload)
        print("✅ Bilhete enviado para o Telegram.")
    except Exception as e:
        print(f"❌ Erro ao enviar Telegram: {e}")