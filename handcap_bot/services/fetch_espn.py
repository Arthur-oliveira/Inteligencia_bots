# services/fetch_espn.py

import requests
from datetime import date, datetime

def fetch_espn_games():
    print("🔄 Buscando dados da ESPN...")

    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    resposta = requests.get(url)
    dados = resposta.json()

    print("✅ Dados recebidos com sucesso!")
    return dados


def parse_espn_games():
    dados = fetch_espn_games()

    jogos_extraidos = []

    events = dados.get("events", [])
    total_jogos = len(events)

    print(f"🎮 Total de jogos encontrados: {total_jogos}")

    for jogo in events:

        info_competicao = jogo["competitions"][0]
        competidores = info_competicao["competitors"]

        # Descobrir quem é mandante e visitante
        mandante = next(t for t in competidores if t["homeAway"] == "home")
        visitante = next(t for t in competidores if t["homeAway"] == "away")

        # -----------------------------
        # 🛠️ Tratamento de Odds/Spread
        # -----------------------------
        spread = "0.0" 
        if "odds" in info_competicao and info_competicao["odds"]:
            try:
                # Tenta pegar o valor 'details' (ex: "LAL -5.5", "-5.5" ou "EVEN")
                raw_spread = info_competicao["odds"][0].get("details", "0.0")
                
                # Se for "EVEN", considera 0.0
                if "EVEN" in str(raw_spread).upper():
                    spread = "0.0"
                else:
                    # Tenta limpar a string para pegar só o número
                    # Ex: "LAL -5.5" -> pega o "-5.5" (último elemento)
                    spread = str(raw_spread).split(" ")[-1]
            except Exception as e:
                print(f"⚠️ Erro ao processar spread: {e}")
                spread = "0.0"

        # -----------------------------
        # ✔️ Conversão correta da data
        # -----------------------------
        data_bruta = jogo.get("date")  # ex: "2025-12-11T03:00Z"
        data_formatada = None

        if data_bruta:
            try:
                # Remover o "Z" e converter
                data_limpa = data_bruta.replace("Z", "+00:00")
                data_dt = datetime.fromisoformat(data_limpa)
                data_formatada = data_dt.strftime("%Y-%m-%d %H:%M:%S")  # Formato postgres
            except Exception as e:
                print(f"⚠️ Erro convertendo data: {data_bruta} -> {e}")
                data_formatada = data_bruta

        # Dicionário com chaves em Português (padrão interno do fetch)
        jogo_formatado = {
            "data_relatorio": str(date.today()),
            "numero_jogos": total_jogos,
            "contexto": "Relatório diário NBA",

            "jogo_id": jogo.get("id"),
            "liga": jogo.get("league", {}).get("name", "NBA"),

            "mandante": mandante["team"]["displayName"],
            "visitante": visitante["team"]["displayName"],

            "data_jogo": data_formatada,
            "handicap_linha": spread, # Valor tratado

            # Campos placeholder (serão preenchidos na strategy)
            "handicap_prob_sucesso": None,
            "handicap_risco": None,
            "handicap_confianca": None,
            "justificativa": None,
            "tendencia": None,
        }

        jogos_extraidos.append(jogo_formatado)

        print("\n-------------------------------")
        print("📌 Jogo coletado:")
        for k, v in jogo_formatado.items():
            print(f"{k}: {v}")

    return jogos_extraidos


if __name__ == "__main__":
    parse_espn_games()