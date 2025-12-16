# app.py

from services.fetch_espn import parse_espn_games
from services.fetch_nba import buscar_estatisticas_avancadas
from services.strategy_handicap import gerar_payload_handicap
from services.notifier_telegram import enviar_notificacao
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import dotenv_values

# ----------------------
# 1. Configurações
# ----------------------
config = dotenv_values(".env")

DB_HOST = config.get("DB_HOST", "192.168.0.195")
DB_USER = config.get("DB_USER", "postgres")
DB_PASSWORD = config.get("DB_PASSWORD", "@#Oliveira")
DB_NAME = config.get("DB_NAME", "inteligencia_bots")
DB_PORT = int(config.get("DB_PORT", 5432))

# ----------------------
# 2. Conexão Banco
# ----------------------
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
        print("❌ Erro ao conectar ao banco:", e)
        return None

# ----------------------
# 3. Inserção
# ----------------------
def inserir_jogo(conn, payload):
    try:
        with conn.cursor() as cur:
            query = """
                INSERT INTO handcap_list(
                    dt_report, num_games, context, game_id, league, 
                    principal, visitor, game_datetime, hp_lines, 
                    hp_prob, hp_risk, hp_conf, justification, trend
                ) VALUES (
                    %(dt_report)s, %(num_games)s, %(context)s, %(game_id)s, %(league)s,
                    %(principal)s, %(visitor)s, %(game_datetime)s, %(hp_lines)s,
                    %(hp_prob)s, %(hp_risk)s, %(hp_conf)s, %(justification)s, %(trend)s
                )
                ON CONFLICT (game_id) DO NOTHING
            """
            cur.execute(query, payload)
            conn.commit()
    except Exception as e:
        print(f"❌ Erro ao inserir jogo {payload.get('game_id')}:", e)
        conn.rollback()

# ----------------------
# 4. Main
# ----------------------
def main():
    conn = conectar_banco()
    if not conn: return

    # Passo A: Inteligência (Stats Históricas)
    nba_stats = buscar_estatisticas_avancadas()
    if not nba_stats:
        print("⚠️ Rodando sem estatísticas avançadas (precisão reduzida).")

    # Passo B: Jogos do Dia (ESPN)
    print("\n🏀 Buscando jogos do dia na ESPN...")
    jogos = parse_espn_games()

    if not jogos:
        print("Nenhum jogo encontrado para hoje.")
        conn.close()
        return

    print(f"\n🔍 Processando {len(jogos)} jogos...")
    relatorio_para_envio = [] 

    # Passo C: Processamento
    for jogo in jogos:
        payload = gerar_payload_handicap(jogo, nba_stats)
        
        # Exibe no terminal apenas o essencial
        print(f" > {payload['principal']} x {payload['visitor']} | {payload['trend']} ({payload['hp_prob']}%)")
        
        inserir_jogo(conn, payload)
        relatorio_para_envio.append(payload)

    # Passo D: Envio Telegram
    print("\n🚀 Enviando relatório para o Telegram...")
    enviar_notificacao(relatorio_para_envio)

    conn.close()
    print("✅ Processo finalizado!")

if __name__ == "__main__":
    main()