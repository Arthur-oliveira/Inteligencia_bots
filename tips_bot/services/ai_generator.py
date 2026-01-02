# C:\inteligencia_bots\tips_bot\services\ai_generator.py
import google.generativeai as genai
import os
from dotenv import dotenv_values

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
config = dotenv_values(env_path)
api_key = config.get("GEMINI_API_KEY")

MSG_PADRAO = "• Ritmo de jogo intenso com transições rápidas.\n• Expectativa de alta eficiência ofensiva de ambos os lados.\n• Tendência de placar elevado baseada no histórico recente."

MODELOS_APROVADOS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite",
    "gemini-flash-lite-latest"
]

def gerar_analise_confronto(mandante, visitante, m_media, v_media):
    """Gera uma frase única mencionando obrigatoriamente os times e focada no futuro."""
    if not api_key: return MSG_PADRAO
    genai.configure(api_key=api_key)
    config_ia = genai.GenerationConfig(temperature=0.8, top_p=0.95, max_output_tokens=150)

    prompt = f"""
    Aja como um analista de NBA experiente. 
    Escreva APENAS UMA FRASE curta e natural sobre o jogo que VAI ACONTECER entre {visitante} e {mandante}.
    
    REGRAS RÍGIDAS:
    1. Você DEVE incluir o nome dos dois times ({visitante} e {mandante}) na frase.
    2. Use o tempo verbal no FUTURO (ex: "vai ser", "promete", "deve").
    3. Proibido textos longos ou listas. Apenas uma linha de impacto.
    4. JAMAIS escreva médias de pontos numéricas.
    5. Comece com um emoji de basquete ou fogo.
    """

    for modelo_nome in MODELOS_APROVADOS:
        try:
            model = genai.GenerativeModel(model_name=modelo_nome, generation_config=config_ia)
            response = model.generate_content(prompt)
            texto = response.text.strip().replace("*", "")
            if texto: return texto
        except: continue
    return f"🏀 {visitante} e {mandante} prometem um duelo intenso com jogadas de tirar o fôlego."

def comentar_jogador_ia(nome_jogador, eh_reserva=False):
    """Gera comentários naturais de até 7 palavras no futuro e sem repetir o nome."""
    if not api_key: return "Promete incendiar a quadra hoje"
    genai.configure(api_key=api_key)
    config_ia = genai.GenerationConfig(temperature=0.9)
    
    contexto = f"O jogador {nome_jogador} assume a responsabilidade pois o principal está fora." if eh_reserva else f"O craque {nome_jogador} chega voando."

    prompt = f"""
    Comente o que o {nome_jogador} VAI fazer no jogo de hoje em no máximo 7 palavras.
    Estilo: Resenha de basquete, natural e focado no FUTURO.
    
    REGRAS:
    1. PROIBIDO repetir o nome "{nome_jogador}". 
    2. PROIBIDO prometer pontos exatos.
    3. Foque na vibe: "vai incendiar a quadra", "domina o garrafão e crava", "explode no ataque hoje".
    """

    for modelo_nome in MODELOS_APROVADOS:
        try:
            model = genai.GenerativeModel(model_name=modelo_nome, generation_config=config_ia)
            response = model.generate_content(prompt)
            res = response.text.strip().replace("*", "").replace("(", "").replace(")", "").replace(".", "")
            if res: return res
        except: continue
    return "Promete comandar as ações ofensivas hoje"