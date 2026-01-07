from datetime import datetime
from services.fetch_data import (
    buscar_jogos_dia,
    media_ultimos_3_jogos,
    buscar_cestinha,
    salvar_cestinha
)
from services.ai_generator import gerar_bilhete
from services.notifier_telegram import enviar_telegram
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def salvar_tip(game, dados):
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT"),
    )
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO tips_list (
            game_id, dt_game, principal, visitor,
            m_media_3, v_media_3,
            m_basket, m_basket_ppg,
            v_basket, v_basket_ppg,
            confronto_analise
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (game_id) DO NOTHING
    """, (
        game["game_id"],
        game["data"],
        dados["mandante"],
        dados["visitante"],
        dados["m_media"],
        dados["v_media"],
        dados["m_basket"],
        dados["m_basket_ppg"],
        dados["v_basket"],
        dados["v_basket_ppg"],
        dados["texto"]
    ))

    conn.commit()
    cur.close()
    conn.close()


def main():
    print(f"\n🚀 INICIANDO PROCESSAMENTO: {datetime.now()}")
    jogos = buscar_jogos_dia()

    for jogo in jogos:
        m = jogo["mandante"]
        v = jogo["visitante"]

        print(f"\n🏀 {m['team']['displayName']} x {v['team']['displayName']}")

        m_media = media_ultimos_3_jogos(m["team"]["id"])
        v_media = media_ultimos_3_jogos(v["team"]["id"])

        print(f"📊 Média últimos 3 jogos: {m_media} / {v_media}")

        m_basket, m_ppg = buscar_cestinha(m["team"]["id"])
        v_basket, v_ppg = buscar_cestinha(v["team"]["id"])

        if m_basket:
            salvar_cestinha(m["team"]["id"], m["team"]["displayName"], m_basket, m_ppg)
        if v_basket:
            salvar_cestinha(v["team"]["id"], v["team"]["displayName"], v_basket, v_ppg)

        texto = gerar_bilhete(
            mandante=m["team"]["displayName"],
            visitante=v["team"]["displayName"],
            m_media=m_media,
            v_media=v_media,
            m_basket=m_basket,
            v_basket=v_basket
        )

        dados = {
            "mandante": m["team"]["displayName"],
            "visitante": v["team"]["displayName"],
            "m_media": m_media,
            "v_media": v_media,
            "m_basket": m_basket,
            "m_basket_ppg": m_ppg,
            "v_basket": v_basket,
            "v_basket_ppg": v_ppg,
            "texto": texto
        }

        salvar_tip(jogo, dados)
        enviar_telegram(texto)


if __name__ == "__main__":
    main()
