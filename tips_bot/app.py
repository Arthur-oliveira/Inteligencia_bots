# app.py
import psycopg2
import sys
from dotenv import dotenv_values
from datetime import datetime

# Serviços
from services.fetch_data import buscar_jogos_hoje, buscar_lesoes, analisar_estatisticas_time
from services.notifier_telegram import enviar_telegram

# Configuração SEGURA via .env
config = dotenv_values(".env")

DB_HOST = config.get("DB_HOST")
DB_USER = config.get("DB_USER")
DB_PASSWORD = config.get("DB_PASSWORD")
DB_NAME = config.get("DB_NAME")
DB_PORT = config.get("DB_PORT")

def conectar_banco():
    # Verifica se as variáveis existem antes de tentar conectar
    if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT]):
        print("❌ ERRO CRÍTICO: Credenciais do banco ausentes no .env")
        return None

    try:
        conn = psycopg2.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"❌ Erro de Conexão DB: {e}")
        return None

def main():
    print("\n🚀 --- INICIANDO TIPS BOT ---")
    
    # 1. Verifica conexão com banco logo no início
    conn = conectar_banco()
    if not conn:
        print("Encerrando por falha no banco.")
        return

    # 2. Busca dados externos
    lesoes_dict = buscar_lesoes()
    jogos_hoje = buscar_jogos_hoje()
    
    if not jogos_hoje:
        print("💤 Nenhum jogo encontrado para hoje.")
        conn.close()
        return

    print(f"\n🔍 Analisando {len(jogos_hoje)} jogos em busca de médias > 100...")

    for jogo in jogos_hoje:
        game_id = jogo['game_id']
        mandante = jogo['mandante_nome']
        visitante = jogo['visitante_nome']
        
        print(f" > Processando: {visitante} x {mandante}...")
        
        # Busca estatísticas
        stats_m = analisar_estatisticas_time(jogo['mandante_id'])
        stats_v = analisar_estatisticas_time(jogo['visitante_id'])
        
        m_media = stats_m['media_3_jogos']
        v_media = stats_v['media_3_jogos']
        
        # LÓGICA: Se algum dos dois tiver média > 100
        if m_media > 100 or v_media > 100:
            print(f"   🔥 OPORTUNIDADE! Médias: {mandante}={m_media:.1f}, {visitante}={v_media:.1f}")
            
            # Prepara dados do Mandante
            m_basket = stats_m['cestinha_1']
            m_reserv = stats_m['cestinha_2']
            m_status = lesoes_dict.get(str(m_basket).lower(), "Active") if m_basket else "Unknown"
            
            # Prepara dados do Visitante
            v_basket = stats_v['cestinha_1']
            v_reserv = stats_v['cestinha_2']
            v_status = lesoes_dict.get(str(v_basket).lower(), "Active") if v_basket else "Unknown"
            
            dados_para_banco = {
                "game_id": game_id,
                "dt_game": datetime.now(),
                "principal": mandante,
                "visitor": visitante,
                "m_media_3": m_media,
                "v_media_3": v_media,
                "m_basket": m_basket,
                "m_status": m_status,
                "m_reserv": m_reserv,
                "v_basket": v_basket,
                "v_status": v_status,
                "v_reserv": v_reserv
            }
            
            salvar_e_notificar(conn, dados_para_banco)
            
        else:
            print(f"   ❄️ Ignorado. Médias: {m_media:.1f} / {v_media:.1f}")

    conn.close()
    print("🏁 Processo finalizado.")

def salvar_e_notificar(conn, dados):
    try:
        cur = conn.cursor()
        
        query = """
            INSERT INTO tips_list (
                game_id, dt_game, principal, visitor, 
                m_media_3, v_media_3, 
                m_basket, m_status, m_reserv, 
                v_basket, v_status, v_reserv
            ) VALUES (
                %(game_id)s, %(dt_game)s, %(principal)s, %(visitor)s,
                %(m_media_3)s, %(v_media_3)s,
                %(m_basket)s, %(m_status)s, %(m_reserv)s,
                %(v_basket)s, %(v_status)s, %(v_reserv)s
            )
            ON CONFLICT (game_id) DO NOTHING
        """
        
        cur.execute(query, dados)
        rows_affected = cur.rowcount
        conn.commit()
        cur.close()
        
        if rows_affected > 0:
            print("   💾 Salvo no banco. Enviando Telegram...")
            enviar_telegram(dados)
        else:
            print("   ⚠️ Jogo já analisado/enviado anteriormente.")
            
    except Exception as e:
        print(f"❌ Erro ao salvar no banco: {e}")
        conn.rollback()

if __name__ == "__main__":
    main()