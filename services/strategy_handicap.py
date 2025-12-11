# services/strategy_handicap.py

import os
import json
import time
import google.generativeai as genai
from datetime import date
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# ==============================================================================
# 🔒 LISTA DE PREFERÊNCIA E RESTRIÇÕES
# ==============================================================================
# Ordem exata de prioridade
MODELOS_PREFERENCIAIS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-flash-lite-latest",
    "models/gemini-flash-latest",
    "gemini-2.0-flash-001"
]

PALAVRAS_CHAVE_PERMITIDAS = ["lite", "flash"]
PALAVRAS_PROIBIDAS = ["pro", "ultra", "advance"]

def listar_modelos_candidatos():
    """
    Retorna uma LISTA ordenada de todos os modelos seguros disponíveis.
    Não retorna apenas um, mas todos que passaram no filtro.
    """
    if not API_KEY:
        print("❌ CRÍTICO: API Key não encontrada.")
        return []

    candidatos_finais = []
    
    try:
        # 1. Obtém tudo que está disponível na conta
        todos_disponiveis = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                todos_disponiveis.append(m.name)

        # 2. Filtra Segurança (Remove PRO/ULTRA)
        seguros = []
        for m in todos_disponiveis:
            if not any(p in m.lower() for p in PALAVRAS_PROIBIDAS):
                seguros.append(m)

        # 3. Adiciona Preferenciais (na ordem correta)
        for pref in MODELOS_PREFERENCIAIS:
            for m in seguros:
                if pref in m and m not in candidatos_finais:
                    candidatos_finais.append(m)

        # 4. Adiciona Alternativos (Flash/Lite genéricos que sobraram)
        for m in seguros:
            if m not in candidatos_finais:
                if any(k in m.lower() for k in PALAVRAS_CHAVE_PERMITIDAS):
                    candidatos_finais.append(m)
        
        return candidatos_finais

    except Exception as e:
        print(f"⚠️ Erro ao listar modelos: {e}")
        # Fallback de emergência se a listagem falhar
        return ["models/gemini-1.5-flash"]

def consultar_gemini(mandante, visitante, data_jogo):
    """
    Tenta TODOS os modelos da lista, um por um.
    Só espera 10 min se todos falharem.
    """
    if not API_KEY:
        return None

    while True: # Loop Infinito (Protocolo de Persistência)
        
        # Passo 1: Atualiza a lista de candidatos
        candidatos = listar_modelos_candidatos()
        
        if not candidatos:
            print("❌ Nenhum modelo seguro encontrado na sua conta.")
            print("⏳ Aguardando 10 minutos para tentar novamente...")
            time.sleep(600)
            continue

        print(f"\n📋 [IA] Fila de modelos para teste: {len(candidatos)} opções identificadas.")
        
        sucesso_total = False

        # Passo 2: Tenta cada modelo da lista sequencialmente
        for modelo_atual in candidatos:
            print(f"👉 [TENTATIVA] Usando modelo: {modelo_atual} ... ", end="")
            
            try:
                model = genai.GenerativeModel(modelo_atual)

                prompt = f"""
                Aja como um Handicapper Profissional da NBA.
                Analise: {mandante} (Casa) vs {visitante} (Fora) em {data_jogo}.

                Tarefas:
                1. Estime a "Linha Justa" (Spread) para o Mandante.
                2. Calcule a probabilidade (%) do Mandante cobrir essa linha.
                3. Defina Risco (BAIXO/MEDIO/ALTO) e Confiança (0-100).

                Responda APENAS um JSON válido neste formato:
                {{
                    "hp_lines": "string (ex: -5.5)",
                    "hp_prob": float (ex: 58.5),
                    "hp_risk": "string",
                    "hp_conf": int,
                    "trend": "string (mandante/visitante/equilibrado)",
                    "justification": "string (Resumo de 1 frase pt-br)"
                }}
                """

                # Timeout curto para não travar se o modelo estiver "pendurado"
                response = model.generate_content(prompt, request_options={"timeout": 30})
                texto_limpo = response.text.replace("```json", "").replace("```", "").strip()
                resultado = json.loads(texto_limpo)
                
                print("✅ SUCESSO!")
                return resultado # <--- SUCESSO! Sai da função e retorna o dado.

            except Exception as e:
                erro = str(e)
                if "429" in erro:
                    print(f"⚠️ FALHA (429 - Limite). Pulando para o próximo...")
                elif "404" in erro:
                    print(f"⚠️ FALHA (404 - Não encontrado). Pulando...")
                else:
                    print(f"❌ ERRO ({erro[:30]}...). Pulando...")
                
                # Não dorme aqui! Tenta o próximo modelo imediatamente.
                continue 

        # Passo 3: Se o código chegou aqui, TODOS os modelos da lista falharam.
        if not sucesso_total:
            print("\n⛔ [BLOQUEIO TOTAL] Todos os modelos da lista falharam ou estão limitados.")
            print("⏳ [PROTOCOLO] Iniciando espera obrigatória de 10 minutos...")
            time.sleep(600)
            print("🔄 [REINÍCIO] Acordando e reiniciando o ciclo de tentativas...\n")
            # O 'while True' vai jogar de volta para o começo da lista

def gerar_payload_handicap(jogo):
    """
    Controlador do fluxo de dados.
    """
    dt_report = date.today()
    num_games = jogo.get("numero_jogos", 1)
    context = jogo.get("contexto", "rodada regular")
    
    game_id = jogo.get("jogo_id")
    league = jogo.get("liga")
    principal = jogo.get("mandante")
    visitor = jogo.get("visitante")
    game_datetime = jogo.get("data_jogo")

    print(f"🤖 Analisando confronto: {principal} x {visitor}...")
    
    # Delay leve antes de começar o ciclo (para não floodar logs)
    time.sleep(2)

    analise_ia = consultar_gemini(principal, visitor, game_datetime)

    if analise_ia:
        hp_lines = analise_ia.get("hp_lines", "+0.0")
        hp_prob = float(analise_ia.get("hp_prob", 50.0))
        hp_risk = analise_ia.get("hp_risk", "MÉDIO")
        hp_conf = int(analise_ia.get("hp_conf", 50))
        trend = analise_ia.get("trend", "equilibrado")
        justification = f"🤖 {analise_ia.get('justification')}"
    else:
        # Teoricamente inalcançável pois o 'consultar_gemini' é infinito
        hp_lines = "+0.0"
        hp_prob = 50.0
        hp_risk = "MÉDIO"
        hp_conf = 50
        trend = "equilibrado"
        justification = "⚠️ Erro fatal."

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