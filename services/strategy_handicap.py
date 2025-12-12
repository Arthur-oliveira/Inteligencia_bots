# services/strategy_handicap.py

import os
import json
import time
import google.generativeai as genai
from datetime import date
from dotenv import load_dotenv

# Carrega variáveis
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# Lista de Modelos
MODELOS_PREFERENCIAIS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-flash-lite-latest",
    "models/gemini-flash-latest",
    "gemini-2.0-flash-001"
]
PALAVRAS_CHAVE_PERMITIDAS = ["lite", "flash"]
PALAVRAS_PROIBIDAS = ["pro", "ultra", "advance"]

def carregar_instrucoes_sistema():
    """
    Lê o arquivo system_instruction.txt da raiz do projeto.
    """
    try:
        # Sobe um nível (..) a partir da pasta services para achar a raiz
        caminho_arquivo = os.path.join(os.path.dirname(__file__), '..', 'system_instruction.txt')
        
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            return conteudo
    except Exception as e:
        print(f"⚠️ Erro ao ler system_instruction.txt: {e}")
        # Retorna uma instrução básica de fallback caso o arquivo não seja lido
        return "Você é um especialista em NBA. Analise o jogo e retorne JSON."

def listar_modelos_candidatos():
    if not API_KEY: return []
    try:
        todos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        seguros = [m for m in todos if not any(p in m.lower() for p in PALAVRAS_PROIBIDAS)]
        
        candidatos = []
        for pref in MODELOS_PREFERENCIAIS:
            for m in seguros:
                if pref in m and m not in candidatos:
                    candidatos.append(m)
        for m in seguros:
            if m not in candidatos and any(k in m.lower() for k in PALAVRAS_CHAVE_PERMITIDAS):
                candidatos.append(m)
        return candidatos
    except:
        return ["models/gemini-1.5-flash"]

def consultar_gemini(mandante, visitante, data_jogo):
    if not API_KEY: return None

    # 1. Carrega a estratégia do seu arquivo de texto
    instrucao_do_sistema = carregar_instrucoes_sistema()

    configuracao_segura = genai.GenerationConfig(
        temperature=0.1, 
        top_p=0.90,
        response_mime_type="application/json"
    )

    while True:
        candidatos = listar_modelos_candidatos()
        if not candidatos:
            time.sleep(600)
            continue

        print(f"\n📋 [IA] Fila de modelos ({len(candidatos)} opções)...")
        sucesso = False

        for modelo_atual in candidatos:
            print(f"👉 [TENTATIVA] {modelo_atual} ... ", end="")
            try:
                # 2. Injeta o arquivo de texto como 'system_instruction'
                model = genai.GenerativeModel(
                    modelo_atual, 
                    generation_config=configuracao_segura,
                    system_instruction=instrucao_do_sistema  # <--- AQUI ESTÁ A MÁGICA
                )

                # 3. Prompt Focado apenas no Jogo + Formato JSON
                # O bot já "leu" o arquivo de texto na linha acima. 
                # Agora só mandamos os dados do jogo.
                prompt = f"""
                ANALISE ESTE JOGO ESPECÍFICO COM BASE NAS SUAS INSTRUÇÕES DE SISTEMA:
                
                CONFRONTO: {mandante} (Casa) vs {visitante} (Fora)
                Data: {data_jogo}

                IMPORTANTE SOBRE FORMATO DE SAÍDA:
                Apesar das instruções de sistema pedirem um relatório em texto, 
                eu preciso EXCLUSIVAMENTE de um JSON para salvar no banco de dados.
                
                Siga a lógica de estratégia (Seções 3 e 4 do arquivo), mas ignore o layout visual (Seção 5).
                
                SCHEMA JSON OBRIGATÓRIO:
                {{
                    "hp_lines": "string (ex: +4.5 ou -3.0)",
                    "hp_prob": float (ex: 58.5),
                    "hp_risk": "string",
                    "hp_conf": int,
                    "trend": "string (mandante/visitante/equilibrado)",
                    "justification": "string (Resumo curto da análise)"
                }}
                """

                response = model.generate_content(prompt, request_options={"timeout": 30})
                resultado = json.loads(response.text.strip())
                
                if isinstance(resultado, list):
                    resultado = resultado[0] if len(resultado) > 0 else None
                
                if resultado:
                    print("✅ SUCESSO!")
                    return resultado

            except Exception as e:
                erro = str(e)
                if "429" in erro: print(f"⚠️ 429 (Limite).")
                else: print(f"❌ Erro: {erro[:20]}...")
                continue

        if not sucesso:
            print("⛔ Todos falharam. Aguardando 10 min...")
            time.sleep(600)

def gerar_payload_handicap(jogo):
    dt_report = date.today()
    num_games = jogo.get("numero_jogos", 1)
    context = jogo.get("contexto", "rodada regular")
    
    game_id = jogo.get("jogo_id")
    league = jogo.get("liga")
    principal = jogo.get("mandante")
    visitor = jogo.get("visitante")
    game_datetime = jogo.get("data_jogo")

    print(f"🤖 Analisando: {principal} x {visitor}...")
    time.sleep(5) 

    analise_ia = consultar_gemini(principal, visitor, game_datetime)

    if analise_ia and isinstance(analise_ia, dict):
        hp_lines = analise_ia.get("hp_lines", "+0.0")
        hp_prob = float(analise_ia.get("hp_prob", 50.0))
        hp_risk = analise_ia.get("hp_risk", "MÉDIO")
        hp_conf = int(analise_ia.get("hp_conf", 50))
        trend = analise_ia.get("trend", "equilibrado")
        justification = f"🤖 {analise_ia.get('justification')}"
    else:
        hp_lines = "+0.0"
        hp_prob = 50.0
        hp_risk = "MÉDIO"
        hp_conf = 50
        trend = "equilibrado"
        justification = "⚠️ Erro fatal na IA."

    payload = {
        "dt_report": dt_report,
        "num_games": num_games,
        "context": context,
        "game_id": game_id,
        "league": league,
        "principal": principal,
        "visitor": visitor,
        "game_datetime": game_datetime,
        "hp_lines": hp_lines,
        "hp_prob": hp_prob,
        "hp_risk": hp_risk,
        "hp_conf": hp_conf,
        "justification": justification,
        "trend": trend
    }

    return payload