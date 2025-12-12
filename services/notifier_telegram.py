# services/notifier_telegram.py

import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, timedelta # <--- Importamos timedelta para corrigir a hora
from dotenv import load_dotenv

# Carrega variáveis
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Configuração do Banco
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

def enviar_mensagem_telegram(mensagem):
    """
    Envia string de texto para o Telegram via API HTTP.
    """
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Configuração de Telegram ausente (.env).")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown" # Permite negrito e itálico
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Relatório enviado para o Telegram!")
        else:
            print(f"⚠️ Erro ao enviar Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão Telegram: {e}")

def gerar_relatorio_diario():
    """
    Busca os jogos processados HOJE no banco e monta o texto final com regras personalizadas.
    """
    hoje = date.today()
    
    try:
        # Conecta ao Banco
        conn = psycopg2.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, 
            database=DB_NAME, port=DB_PORT
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Busca jogos de hoje
        query = """
            SELECT * FROM handcap_list 
            WHERE dt_report = %s 
            ORDER BY game_datetime ASC
        """
        cur.execute(query, (hoje,))
        jogos = cur.fetchall()
        
        conn.close()

        if not jogos:
            print("📭 Nenhum jogo encontrado no banco para hoje.")
            return

        # ==========================================
        # 📝 MONTAGEM DO TEXTO (FORMATO FINAL)
        # ==========================================
        texto_final = f"📊 *RELATÓRIO DIÁRIO — HANDICAP NBA*\n"
        texto_final += f"📅 Data: {hoje.strftime('%d/%m/%Y')}\n"
        texto_final += f"──────────────────────\n\n"

        for jogo in jogos:
            # 1. Correção de Horário (UTC -> Brasília -3h)
            # O banco retorna um objeto datetime. Subtraímos 3 horas.
            dt_brasil = jogo['game_datetime'] - timedelta(hours=3)
            hora_jogo = dt_brasil.strftime('%H:%M')
            
            # 2. Nova Lógica de Risco baseada na Confiança (hp_conf)
            confianca = jogo['hp_conf'] if jogo['hp_conf'] is not None else 0
            
            if confianca <= 50:
                risco_texto = "ALTO"
                emoji_risco = "🔴" # Vermelho
            elif confianca <= 70:
                risco_texto = "MÉDIO"
                emoji_risco = "🟠" # Laranja
            else:
                risco_texto = "BAIXO"
                emoji_risco = "🟢" # Verde
            
            # Lógica de Sugestão Visual
            linha = jogo['hp_lines']
            
            texto_final += f"🏀 *{jogo['visitor']}* @ *{jogo['principal']}*\n"
            texto_final += f"⏰ Horário: {hora_jogo}\n"
            texto_final += f"📉 *Linha (Handicap):* {linha}\n"
            texto_final += f"🧠 *Probabilidade:* {jogo['hp_prob']}%\n"
            texto_final += f"{emoji_risco} *Risco:* {risco_texto}\n" 
            texto_final += f"📝 *Análise:* {jogo['justification'].replace('🤖 ', '')}\n" 
            texto_final += f"──────────────────────\n\n"

        # Envia (Sem rodapé de resumo)
        print("\n📨 Enviando relatório para o Telegram...")
        enviar_mensagem_telegram(texto_final)

    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {e}")

# Teste local se rodar o arquivo direto
if __name__ == "__main__":
    gerar_relatorio_diario()