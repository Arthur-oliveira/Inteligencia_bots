# app.py

import time
import schedule
import psycopg2
from services.fetch_espn import parse_espn_games
from services.strategy_handicap import gerar_payload_handicap
from services.notifier_telegram import gerar_relatorio_diario
from psycopg2.extras import RealDictCursor
from dotenv import dotenv_values
from datetime import datetime

# ----------------------
# 1. Carrega variáveis e Configurações
# ----------------------
config = dotenv_values(".env")

DB_HOST = config.get("DB_HOST", "192.168.0.195")
DB_USER = config.get("DB_USER", "postgres")
DB_PASSWORD = config.get("DB_PASSWORD", "@#Oliveira")
DB_NAME = config.get("DB_NAME", "inteligencia_bots")
DB_PORT = int(config.get("DB_PORT", 5432))

def conectar_banco():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            options="-c client_encoding=UTF8",
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print("❌ Erro crítico ao conectar ao banco:", e)
        return None

def inserir_jogo(conn, payload):
    try:
        with conn.cursor() as cur:
            query = """
                INSERT INTO handcap_list(
                    dt_report, num_games, context, game_id, league, principal, visitor,
                    game_datetime, hp_lines, hp_prob, hp_risk, hp_conf, justification, trend
                ) VALUES (
                    %(dt_report)s, %(num_games)s, %(context)s, %(game_id)s, %(league)s,
                    %(principal)s, %(visitor)s, %(game_datetime)s, %(hp_lines)s,
                    %(hp_prob)s, %(hp_risk)s, %(hp_conf)s, %(justification)s, %(trend)s
                )
                ON CONFLICT (game_id) DO NOTHING
            """
            cur.execute(query, payload)
            conn.commit()
            print(f"✅ Jogo {payload['game_id']} salvo.")
    except Exception as e:
        print("❌ Erro ao inserir jogo:", e)
        conn.rollback()

# ----------------------
# 2. A Tarefa Principal (O que o bot faz)
# ----------------------
def tarefa_do_bot():
    print(f"\n⏰ Iniciando execução agendada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("🏀 --- RODANDO HANDICAP BOT NBA --- 🏀")
    
    conn = conectar_banco()
    if not conn:
        return

    # A. Busca Jogos
    print("📡 Buscando jogos na ESPN...")
    jogos = parse_espn_games()

    # B. Processa IA
    print("🧠 Processando estratégias com IA...")
    if jogos:
        for jogo in jogos:
            payload = gerar_payload_handicap(jogo)
            inserir_jogo(conn, payload)
    else:
        print("⚠️ Nenhum jogo encontrado hoje.")

    conn.close()
    
    # C. Envia Telegram
    print("📲 Gerando e enviando relatório Telegram...")
    gerar_relatorio_diario()
    
    print("🏁 Execução finalizada! Aguardando próximo agendamento...")

# ----------------------
# 3. O Agendador (Loop Infinito)
# ----------------------
def main():
    # Define o horário (Formato 24h)
    HORARIO_AGENDADO = "22:35"
    
    print(f"🤖 Bot iniciado em modo automático.")
    print(f"📅 O relatório será enviado todo dia às {HORARIO_AGENDADO} (Horário do Sistema).")
    print("⏳ Aguardando horário... (Não feche esta janela)")

    # Agenda a tarefa
    schedule.every().day.at(HORARIO_AGENDADO).do(tarefa_do_bot)

    # Loop para manter o script vivo verificando a hora
    while True:
        schedule.run_pending()
        time.sleep(60) # Verifica a cada 1 minuto para economizar CPU

if __name__ == "__main__":
    main()