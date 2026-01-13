import requests
import os
from dotenv import load_dotenv
from database.database_manager import log

# Carrega as variáveis do seu arquivo .env
load_dotenv()

# Mapeamento exato das chaves do seu arquivo .env
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def enviar_mensagem_telegram(mensagem):
    """
    Envia o bilhete formatado ou o alerta de choque para o grupo do Telegram.
    Utiliza HTML para negritos e emojis conforme o manual.
    """
    if not TOKEN or not CHAT_ID:
        log.error("❌ Erro crítico: TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID ausentes no .env")
        return False

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # Montagem do pacote de dados para a API do Telegram
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML",
        "disable_web_page_preview": True # Mantém o chat limpo sem links grandes
    }

    try:
        log.info("📤 Tentando enviar notificação para o Telegram...")
        response = requests.post(url, data=payload, timeout=15)
        
        if response.status_code == 200:
            log.info("✅ Mensagem entregue ao grupo com sucesso!")
            return True
        else:
            log.error(f"❌ Falha no Telegram (Status {response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        log.error(f"❌ Erro de conexão ao tentar falar com o Telegram: {e}")
        return False

# Bloco de teste rápido: Rode este arquivo diretamente para ver se apita no celular
if __name__ == "__main__":
    teste_msg = "🚀 <b>BOT ONLINE!</b>\nO sistema de Tips NBA 2025/26 foi conectado com sucesso ao Telegram."
    enviar_mensagem_telegram(teste_msg)