import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os
import math
from dotenv import load_dotenv
from datetime import datetime

# 📂 CONFIGURAÇÃO DE LOGS
def setup_bot_logs():
    log_dir = r"C:\Inteligencia_bots\tips_bot\log"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, f"bot_log_{datetime.now().strftime('%Y-%m-%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("TipsBot")

log = setup_bot_logs()

# 🔐 CONEXÃO COM POSTGRESQL (Dados do seu .env)
load_dotenv()
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT")
}

def executar_query(sql, params=None):
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                conn.commit()
                return True
    except Exception as e:
        log.error(f"Erro ao executar query: {e}")
        return False

def buscar_dados(sql, params=None):
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                return cur.fetchall()
    except Exception as e:
        log.error(f"Erro ao buscar dados: {e}")
        return []

def calcular_palpite_par(media):
    """
    Aplica a lógica de arredondamento e segurança:
    $Entrada = \lfloor Média \rfloor - (2 \text{ se Par}, 3 \text{ se Ímpar})$.
    """
    valor_base = math.floor(float(media))
    if valor_base % 2 == 0:
        return int(valor_base - 2)
    return int(valor_base - 3)