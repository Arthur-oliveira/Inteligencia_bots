# C:\inteligencia_bots\tips_bot\services\ai_generator.py
import google.generativeai as genai
from dotenv import dotenv_values

# Carrega a API KEY do .env
config = dotenv_values(".env")
api_key = config.get("GEMINI_API_KEY")

def gerar_analise_confronto(mandante, visitante, m_media, v_media):
    """
    Usa o Gemini para gerar análise com temperatura controlada.
    Se falhar, retorna texto padrão fixo.
    """
    
    # MENSAGEM PADRÃO (Caso a IA falhe ou não tenha chave)
    MSG_PADRAO = "• Ritmo de jogo intenso.\n\n• Tendência de placar alto."

    if not api_key:
        return MSG_PADRAO

    genai.configure(api_key=api_key)

    # 1. CONTROLE DE TEMPERATURA (ANTI-ALUCINAÇÃO)
    # temperature 0.2 = Muito focado/conservador (Evita invenções)
    config_ia = genai.GenerationConfig(
        temperature=0.2,
        top_p=0.95,
        top_k=40,
        max_output_tokens=300,
    )

    # 2. LISTA RÍGIDA DE MODELOS APROVADOS
    # O robô tentará estritamente nesta ordem.
    modelos_aprovados = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
        "gemini-2.0-flash-lite",
        "gemini-flash-lite-latest"
    ]

    # Contexto para o prompt
    contexto = ""
    if m_media > 100 and v_media > 100:
        contexto = "Ambos os times com ataques fortes (média > 100). Jogo rápido."
    elif m_media > 100:
        contexto = f"Apenas o {mandante} vem forte no ataque."
    elif v_media > 100:
        contexto = f"Apenas o {visitante} vem forte no ataque."

    prompt = f"""
    Aja como um analista especialista em NBA.
    Escreva 1 bullet points curto sobre o jogo: {visitante} vs {mandante}.
    
    DADOS:
    - Média {visitante}: {v_media:.1f} pts
    - Média {mandante}: {m_media:.1f} pts
    - Contexto: {contexto}

    REGRAS RÍGIDAS:
    1. Use emojis no início.
    2. Fale de ritmo, ataque e defesa.
    3. NÃO invente lesões ou dados que não estão aqui.
    4. Seja direto. Sem enrolação.
    """

    # 3. LOOP DE TENTATIVA (Tenta apenas os aprovados)
    for modelo_nome in modelos_aprovados:
        try:
            # print(f"   🤖 Tentando modelo: {modelo_nome}...") # Debug opcional
            model = genai.GenerativeModel(
                model_name=modelo_nome,
                generation_config=config_ia
            )
            response = model.generate_content(prompt)
            
            # Validação simples: se vier vazio, força erro para tentar o próximo
            texto = response.text.strip()
            if not texto: raise Exception("Resposta vazia da IA")
            
            return texto
        
        except Exception as e:
            print(f"   ⚠️ Falha com {modelo_nome}: {e}")
            continue # Pula para o próximo modelo da lista

    # 4. FALLBACK FINAL (Se todos falharem)
    print("   ❌ IA indisponível. Usando mensagem padrão.")
    return MSG_PADRAO