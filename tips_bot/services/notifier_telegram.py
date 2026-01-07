import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def enviar_telegram(texto):
    """
    Envia TEXTO pronto para o Telegram.
    Não monta bilhete.
    Não interpreta dados.
    """

    if not texto:
        print("⚠️ Texto vazio. Nada enviado ao Telegram.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto,
        "parse_mode": "HTML"
    }

    try:
        resp = requests.post(url, data=payload, timeout=10)

        if resp.status_code == 200:
            print("📨 Bilhete enviado ao Telegram com sucesso.")
        else:
            print(f"❌ Erro Telegram: {resp.status_code} - {resp.text}")

    except Exception as e:
        print(f"❌ Falha ao enviar Telegram: {e}")
