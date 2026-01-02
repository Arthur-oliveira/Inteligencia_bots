# C:\inteligencia_bots\tips_bot\app.py
import psycopg2
import os
import schedule
import time
from dotenv import dotenv_values
from datetime import datetime
from services.fetch_data import buscar_jogos_hoje, buscar_lesoes, analisar_estatisticas_time
from services.notifier_telegram import enviar_telegram, enviar_lista_agenda
from services.ai_generator import gerar_analise_confronto, comentar_jogador_ia

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config = dotenv_values(os.path.join(BASE_DIR, ".env"))

def tarefa_completa():
    print(f"\n🚀 INICIANDO BOT: {datetime.now().strftime('%H:%M:%S')}")
    lesoes = buscar_lesoes()
    jogos = buscar_jogos_hoje()
    
    if jogos: enviar_lista_agenda(jogos)
    
    for jogo in jogos:
        mandante, visitante = jogo['mandante_nome'], jogo['visitante_nome']
        stats_m = analisar_estatisticas_time(mandante)
        stats_v = analisar_estatisticas_time(visitante)
        m_media, v_media = stats_m['media_3_jogos'], stats_v['media_3_jogos']
        
        if m_media > 100 or v_media > 100:
            # Mandante
            c_m = stats_m['cestinhas']
            m_is_out = "out" in str(lesoes.get(c_m[0]['nome'].lower(), "")).lower()
            m_final = c_m[1] if m_is_out else c_m[0]
            
            # Visitante
            c_v = stats_v['cestinhas']
            v_is_out = "out" in str(lesoes.get(c_v[0]['nome'].lower(), "")).lower()
            v_final = c_v[1] if v_is_out else c_v[0]

            dados = {
                "game_id": jogo['game_id'], "principal": mandante, "visitor": visitante,
                "m_media_3": m_media, "v_media_3": v_media,
                "confronto_analise": gerar_analise_confronto(mandante, visitante, m_media, v_media),
                "m_basket": m_final['nome'], "m_comentario": comentar_jogador_ia(m_final['nome'], m_is_out),
                "v_basket": v_final['nome'], "v_comentario": comentar_jogador_ia(v_final['nome'], v_is_out),
                "m_final_nome": m_final['nome'], "m_final_ppg": m_final['ppg'],
                "v_final_nome": v_final['nome'], "v_final_ppg": v_final['ppg']
            }
            enviar_telegram(dados)
            print(f"✅ Enviado: {visitante} x {mandante}")

if __name__ == "__main__":
    tarefa_completa()