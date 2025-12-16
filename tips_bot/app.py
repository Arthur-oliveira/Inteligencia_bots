import psycopg2
import sys
from dotenv import dotenv_values
from datetime import datetime
from services.fetch_data import buscar_jogos_hoje, buscar_lesoes, analisar_estatisticas_time
from services.notifier_telegram import enviar_telegram
# Importa o novo serviço de IA
from services.ai_generator import gerar_analise_confronto

config = dotenv_values(".env")
DB_HOST = config.get("DB_HOST")
DB_USER = config.get("DB_USER")
DB_PASSWORD = config.get("DB_PASSWORD")
DB_NAME = config.get("DB_NAME")
DB_PORT = config.get("DB_PORT")

def conectar_banco():
    if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT]):
        print("❌ Credenciais ausentes no .env")
        return None
    try:
        return psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, port=DB_PORT)
    except Exception as e:
        print(f"❌ Erro DB: {e}")
        return None

def main():
    print("\n🚀 --- INICIANDO TIPS BOT (COM IA) ---")
    conn = conectar_banco()
    if not conn: return

    lesoes_dict = buscar_lesoes()
    jogos_hoje = buscar_jogos_hoje()
    
    if not jogos_hoje:
        print("💤 Nenhum jogo hoje.")
        conn.close()
        return

    print(f"\n🔍 Analisando {len(jogos_hoje)} jogos...")

    for jogo in jogos_hoje:
        game_id = jogo['game_id']
        mandante = jogo['mandante_nome']
        visitante = jogo['visitante_nome']
        
        print(f" > {visitante} x {mandante}...")
        
        stats_m = analisar_estatisticas_time(mandante)
        stats_v = analisar_estatisticas_time(visitante)
        
        m_media = stats_m['media_3_jogos']
        v_media = stats_v['media_3_jogos']
        
        if m_media > 100 or v_media > 100:
            print(f"   🔥 GATILHO! Médias: {m_media:.1f} / {v_media:.1f}")
            
            # --- CHAMADA DA IA AQUI ---
            print("   🤖 Gerando análise com Gemini...")
            texto_confronto = gerar_analise_confronto(mandante, visitante, m_media, v_media)
            
            # Extraindo Cestinhas
            c_m = stats_m['cestinhas']
            m_basket = c_m[0]['nome']
            m_ppg    = c_m[0]['ppg']
            m_reserv = c_m[1]['nome']
            m_reserv_ppg = c_m[1]['ppg']
            
            c_v = stats_v['cestinhas']
            v_basket = c_v[0]['nome']
            v_ppg    = c_v[0]['ppg']
            v_reserv = c_v[1]['nome']
            v_reserv_ppg = c_v[1]['ppg']

            m_status = lesoes_dict.get(str(m_basket).lower(), "Active") if m_basket != "N/A" else "Unknown"
            v_status = lesoes_dict.get(str(v_basket).lower(), "Active") if v_basket != "N/A" else "Unknown"
            
            dados = {
                "game_id": game_id,
                "dt_game": datetime.now(),
                "principal": mandante, "visitor": visitante,
                "m_media_3": m_media, "v_media_3": v_media,
                # Campo Novo da IA
                "confronto_analise": texto_confronto,
                
                "m_basket": m_basket, "m_basket_ppg": m_ppg,
                "m_status": m_status,
                "m_reserv": m_reserv, "m_reserv_ppg": m_reserv_ppg,
                "v_basket": v_basket, "v_basket_ppg": v_ppg,
                "v_status": v_status, "v_reserv": v_reserv, "v_reserv_ppg": v_reserv_ppg
            }
            
            salvar_e_notificar(conn, dados)
        else:
            print(f"   ❄️ Ignorado.")

    conn.close()
    print("🏁 Fim.")

def salvar_e_notificar(conn, dados):
    try:
        cur = conn.cursor()
        query = """
            INSERT INTO tips_list (
                game_id, dt_game, principal, visitor, 
                m_media_3, v_media_3, confronto_analise,
                m_basket, m_basket_ppg, m_status, m_reserv, m_reserv_ppg,
                v_basket, v_basket_ppg, v_status, v_reserv, v_reserv_ppg
            ) VALUES (
                %(game_id)s, %(dt_game)s, %(principal)s, %(visitor)s,
                %(m_media_3)s, %(v_media_3)s, %(confronto_analise)s,
                %(m_basket)s, %(m_basket_ppg)s, %(m_status)s, %(m_reserv)s, %(m_reserv_ppg)s,
                %(v_basket)s, %(v_basket_ppg)s, %(v_status)s, %(v_reserv)s, %(v_reserv_ppg)s
            )
            ON CONFLICT (game_id) DO NOTHING
        """
        cur.execute(query, dados)
        rows = cur.rowcount
        conn.commit()
        cur.close()
        
        if rows > 0:
            print("   💾 Salvo. Enviando Telegram...")
            enviar_telegram(dados)
        else:
            print("   ⚠️ Jogo já enviado anteriormente.")
    except Exception as e:
        print(f"❌ Erro DB: {e}")
        conn.rollback()

if __name__ == "__main__":
    main()