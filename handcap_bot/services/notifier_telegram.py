# services/notifier_telegram.py
import requests
from dotenv import dotenv_values

# Carrega configurações
config = dotenv_values(".env")
TOKEN = config.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = config.get("TELEGRAM_CHAT_ID")

def formatar_relatorio(lista_payloads):
    if not lista_payloads:
        return "Nenhum jogo analisado hoje."

    relatorio = "🏀 **NBA - DICAS DO DIA** 🏀\n\n"
    
    # Ordena: Melhores oportunidades primeiro
    lista_payloads.sort(key=lambda x: x['hp_prob'], reverse=True)
    
    sugestoes_feitas = 0
    jogos_validos = 0

    for jogo in lista_payloads:
        # FILTRO DE SEGURANÇA:
        # Se os Net Ratings forem 0.0, significa que não achou estatística.
        # Pula esse jogo para não poluir o grupo.
        if jogo.get('m_net_rtg') == 0.0 and jogo.get('v_net_rtg') == 0.0:
            continue
            
        jogos_validos += 1
        mandante = jogo['principal']
        visitante = jogo['visitor']
        trend = jogo['trend']
        linha_oficial = jogo['hp_lines']
        prob = jogo['hp_prob']
        confianca = jogo['hp_conf']
        
        # Formata hora (pega apenas HH:MM)
        try: hora = str(jogo['game_datetime']).split(' ')[1][:5]
        except: hora = "??:??"

        # --- MONTAGEM DO BLOCO ---
        relatorio += f"⚔️ **{visitante} @ {mandante}** ({hora})\n"

        # Se tiver tendência clara e ainda não enviamos 5 dicas
        if trend != "equilibrado" and sugestoes_feitas < 5:
            time_aposta = mandante if trend == "mandante" else visitante
            
            emoji_conf = "🔥" if prob >= 60 else "⚠️"
            
            relatorio += f"✅ **APOSTA:** {time_aposta}\n"
            relatorio += f"📊 **Confiança:** {confianca}% {emoji_conf}\n"
            relatorio += f"📉 **Linha:** {linha_oficial}\n"
            sugestoes_feitas += 1
        else:
            relatorio += f"👀 **Jogo Equilibrado / Sem Valor**\n"
            relatorio += f"📉 Linha: {linha_oficial}\n"

        relatorio += "---------------------------\n"

    relatorio += "\n_As odds e linhas podem mudar._"
    
    if jogos_validos == 0:
        return "⚠️ Erro: Jogos encontrados na ESPN, mas sem correspondência de estatísticas."

    return relatorio

def enviar_notificacao(lista_payloads):
    if not TOKEN or not CHAT_ID:
        print("❌ [Telegram] Token ou Chat ID ausentes.")
        return
    
    msg = formatar_relatorio(lista_payloads)
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": msg, 
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(url, json=payload)
        print("✅ Relatório enviado para o Telegram.")
    except Exception as e:
        print(f"❌ Erro ao enviar Telegram: {e}")