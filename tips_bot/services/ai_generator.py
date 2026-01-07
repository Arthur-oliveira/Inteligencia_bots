import os
import random
from dotenv import load_dotenv

load_dotenv()

# ======================
# GERADOR DE BILHETE
# ======================
def gerar_bilhete(
    mandante,
    visitante,
    m_media,
    v_media,
    m_basket,
    v_basket
):
    confronto_templates = [
        f"{mandante} chega com ataque eficiente e bom aproveitamento recente, enquanto {visitante} tenta equilibrar o confronto com intensidade defensiva. Jogo com tendência ofensiva.",
        f"Confronto interessante entre {mandante} e {visitante}, com ambos apresentando ritmo acelerado nos últimos jogos e boas opções ofensivas.",
        f"{mandante} vem mostrando consistência ofensiva, enquanto {visitante} aposta na velocidade e transição rápida para pontuar.",
        f"{visitante} enfrenta um desafio fora de casa contra {mandante}, que tem mantido médias elevadas e bom controle de jogo.",
        f"Duelo que promete pontos, com {mandante} e {visitante} apresentando ataques produtivos nas últimas partidas."
    ]

    confronto = random.choice(confronto_templates)

    entradas = []

    if m_media >= 110:
        entradas.append(f"🏀 {mandante} 110+ pontos")
    if v_media >= 110:
        entradas.append(f"🏀 {visitante} 110+ pontos")

    if m_basket:
        entradas.append(f"👤 {m_basket} 20+ pontos")
    if v_basket:
        entradas.append(f"👤 {v_basket} 20+ pontos")

    texto = f"""
🏀 {mandante} x {visitante}

📊 CONFRONTO
🏀🔥 {confronto}

⭐️ DESTAQUES
🔥 {m_basket if m_basket else "Sem destaque definido"}
🔥 {v_basket if v_basket else "Sem destaque definido"}

🔥 POSSÍVEIS ENTRADAS
""" + "\n".join(entradas)

    return texto.strip()
