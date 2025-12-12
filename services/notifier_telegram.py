# services/notifier_telegram.py

import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, timedelta
from dotenv import load_dotenv

# Carrega variáveis de ambiente
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
        "parse_mode": "Markdown"
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
    Gera o relatório diário com ajustes de visualização e nome do time na linha.
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
        # 📝 MONTAGEM DO TEXTO
        # ==========================================
        texto_final = f"📊 *RELATÓRIO DIÁRIO — HANDICAP NBA*\n"
        texto_final += f"📅 Data: {hoje.strftime('%d/%m/%Y')}\n"
        texto_final += f"──────────────────────\n\n"

        for jogo in jogos:
            # 1. Ajuste de Horário (UTC-3 para Brasília)
            dt_brasil = jogo['game_datetime'] - timedelta(hours=3)
            hora_jogo = dt_brasil.strftime('%H:%M')
            
            # 2. Definição Visual do Risco (Cores)
            confianca = jogo['hp_conf'] if jogo['hp_conf'] is not None else 0
            
            if confianca <= 50:
                risco_texto = "ALTO"
                emoji_risco = "🔴"
            elif confianca <= 70:
                risco_texto = "MÉDIO"
                emoji_risco = "🟠"
            else:
                risco_texto = "BAIXO"
                emoji_risco = "🟢"

            # 3. Lógica das Linhas (Com Nome do Time)
            mandante = jogo['principal']
            linha_str = jogo['hp_lines'] # Ex: "-3.0"
            
            try:
                # Converte para float para calcular a inflada e formatar sinais
                valor_linha = float(linha_str)
                valor_inflada = valor_linha - 7.5
                
                # Formata com sinal de + se for positivo
                fmt_original = f"+{valor_linha}" if valor_linha > 0 else f"{valor_linha}"
                fmt_inflada = f"+{valor_inflada}" if valor_inflada > 0 else f"{valor_inflada:.1f}"
                
                # --- CORREÇÃO SOLICITADA: NOME DO TIME EXPLÍCITO ---
                linha_display = f"{mandante} {fmt_original}"
                linha_inflada_display = f"{mandante} {fmt_inflada}"
                
            except:
                # Fallback caso não consiga converter número
                linha_display = f"{mandante} {linha_str}"
                linha_inflada_display = "N/A"

            # 4. Monta o Bloco do Jogo
            texto_final += f"🏀 *{jogo['visitor']}* @ *{jogo['principal']}*\n"
            texto_final += f"⏰ Horário: {hora_jogo}\n"
            texto_final += f"📉 *Linha (Handicap):* {linha_display}\n"
            texto_final += f"🚀 *Linha Inflada:* {linha_inflada_display}\n"
            texto_final += f"🧠 *Probabilidade:* {jogo['hp_prob']}%\n"
            texto_final += f"{emoji_risco} *Risco:* {risco_texto}\n" 
            texto_final += f"📝 *Análise:* {jogo['justification'].replace('🤖 ', '')}\n" 
            texto_final += f"──────────────────────\n\n"

        # Envia para o Telegram
        print("\n📨 Enviando relatório para o Telegram...")
        enviar_mensagem_telegram(texto_final)

    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {e}")

if __name__ == "__main__":
    gerar_relatorio_diario()