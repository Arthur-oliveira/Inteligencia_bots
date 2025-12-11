# app.py

from services.fetch_espn import parse_espn_games
from services.strategy_handicap import gerar_payload_handicap
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import dotenv_values

# ----------------------
# 1. Carrega variáveis do .env (UTF-8 seguro)
# ----------------------
config = dotenv_values(".env")

DB_HOST = config.get("DB_HOST", "192.168.0.195")
DB_USER = config.get("DB_USER", "postgres")
DB_PASSWORD = config.get("DB_PASSWORD", "@#Oliveira")
DB_NAME = config.get("DB_NAME", "inteligencia_bots")
DB_PORT = int(config.get("DB_PORT", 5432))

# ----------------------
# 2. Conecta ao PostgreSQL
# ----------------------
def conectar_banco():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            options="-c client_encoding=UTF8",  # força UTF-8
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print("Erro ao conectar ao banco:", e)
        return None

# ----------------------
# 3. Função para inserir payload no banco
# ----------------------
def inserir_jogo(conn, payload):
    try:
        with conn.cursor() as cur:
            query = """
                INSERT INTO handcap_list(
                    dt_report,
                    num_games,
                    context,
                    game_id,
                    league,
                    principal,
                    visitor,
                    game_datetime,
                    hp_lines,
                    hp_prob,
                    hp_risk,
                    hp_conf,
                    justification,
                    trend
                ) VALUES (
                    %(dt_report)s,
                    %(num_games)s,
                    %(context)s,
                    %(game_id)s,
                    %(league)s,
                    %(principal)s,
                    %(visitor)s,
                    %(game_datetime)s,
                    %(hp_lines)s,
                    %(hp_prob)s,
                    %(hp_risk)s,
                    %(hp_conf)s,
                    %(justification)s,
                    %(trend)s
                )
                ON CONFLICT (game_id) DO NOTHING
            """
            cur.execute(query, payload)
            conn.commit()
            print(f"Jogo {payload['game_id']} inserido com sucesso.")
    except Exception as e:
        print("Erro ao inserir jogo:", e)
        conn.rollback()

# ----------------------
# 4. Função principal
# ----------------------
def main():
    conn = conectar_banco()
    if not conn:
        return

    jogos = parse_espn_games()  # pega os jogos do dia já formatados

    for jogo in jogos:
        payload = gerar_payload_handicap(jogo)  # gera payload com novos nomes
        print(payload)  # mostrar no terminal para conferência
        inserir_jogo(conn, payload)

    conn.close()
    print("Processo finalizado!")

# ----------------------
# 5. Executa
# ----------------------
if __name__ == "__main__":
    main()
