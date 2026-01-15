from database.database_manager import log, executar_query, buscar_dados
from endpoints.api_handler import get_league_rankings, get_all_injured_players

def realizar_upsert_nba():
    """
    Alimenta o banco e ATUALIZA A BLACKLIST VIA SCRAPING.
    """
    log.info("🔄 Iniciando ciclo de atualização de dados NBA...")

    # =========================================================================
    # 1. ATUALIZAÇÃO DA TABELA DE LESÕES (Scraping)
    # =========================================================================
    log.info("🚑 Baixando dados reais de lesões (Web Scraping)...")
    lesionados = get_all_injured_players()
    
    if lesionados:
        # Limpa para garantir apenas status atual
        executar_query("TRUNCATE TABLE injuries;")
        
        count_injuries_loop = 0
        for item in lesionados:
            # Inserção baseada em NOME (Primary Key agora é player_name)
            sql_injury = """
                INSERT INTO injuries (player_name, status, details) 
                VALUES (%s, %s, %s)
                ON CONFLICT (player_name) DO UPDATE SET 
                    status = EXCLUDED.status, 
                    details = EXCLUDED.details,
                    updated_at = CURRENT_TIMESTAMP;
            """
            executar_query(sql_injury, (
                item['player_name'], 
                item['status'], 
                item['details']
            ))
            count_injuries_loop += 1
        log.info(f"✅ Tabela 'injuries' atualizada com {count_injuries_loop} jogadores.")
    else:
        log.warning("⚠️ Scraping não retornou dados (Lista vazia).")

    # =========================================================================
    # 🔍 [AUDITORIA] VERIFICAÇÃO NO LOG (PROVA REAL)
    # =========================================================================
    try:
        res_count = buscar_dados("SELECT COUNT(*) as total FROM injuries")
        total_db = res_count[0]['total'] if res_count else 0
        log.info(f"🔍 [AUDITORIA] STATUS DO BANCO: Existem {total_db} jogadores na tabela 'injuries'.")
        
        if total_db > 0:
            # Tenta pegar o Jokic especificamente para te mostrar
            res_jokic = buscar_dados("SELECT player_name, status FROM injuries WHERE player_name ILIKE '%Jokic%' LIMIT 1")
            if res_jokic:
                log.info(f"🔍 [AUDITORIA] ALVO CONFIRMADO: {res_jokic[0]['player_name']} está com status '{res_jokic[0]['status']}'")
            else:
                # Se não achar o Jokic, mostra aleatórios
                res_ex = buscar_dados("SELECT player_name, status FROM injuries ORDER BY RANDOM() LIMIT 3")
                txt = ", ".join([f"{r['player_name']} ({r['status']})" for r in res_ex])
                log.info(f"🔍 [AUDITORIA] Exemplos Aleatórios: {txt}...")
    except Exception as e:
        log.error(f"Erro auditoria: {e}")

    # =========================================================================
    # 2. ATUALIZAÇÃO DOS RANKINGS (Top 50)
    # =========================================================================
    log.info("📊 Sincronizando estatísticas de desempenho...")
    atletas = get_league_rankings()
    
    if not atletas:
        log.warning("⚠️ Nenhum dado de ranking recebido.")
        return

    count_updated = 0
    for i, item in enumerate(atletas):
        atleta = item.get('athlete', {})
        pid = atleta.get('id')
        nome = atleta.get('displayName')
        equipe = atleta.get('teamName', 'N/A')
        sigla = atleta.get('teamShortName', 'N/A')

        if not pid: continue

        # --- DADOS OFENSIVOS ---
        off = next((c['totals'] for c in item['categories'] if c['name'] == 'offensive'), [])
        if off:
            ppg, t_pct = float(off[0]), float(off[6])
            sql_off = """
                INSERT INTO league_offensive_rankings (player_id, player_name, team, team_abbreviation, avg_points, three_point_pct, rank_position)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_name) DO UPDATE SET 
                    player_id = EXCLUDED.player_id,
                    avg_points = EXCLUDED.avg_points, 
                    rank_position = EXCLUDED.rank_position, 
                    last_updated = CURRENT_TIMESTAMP;
            """
            executar_query(sql_off, (pid, nome, equipe, sigla, ppg, t_pct, i+1))

        # --- DADOS DEFENSIVOS ---
        defen = next((c['totals'] for c in item['categories'] if c['name'] == 'defensive'), [])
        if defen:
            stl, blk = float(defen[0]), float(defen[1])
            sql_def = """
                INSERT INTO league_defensive_rankings (player_id, player_name, team, team_abbreviation, avg_steals, avg_blocks, rank_position)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_name) DO UPDATE SET 
                    player_id = EXCLUDED.player_id,
                    avg_steals = EXCLUDED.avg_steals, 
                    avg_blocks = EXCLUDED.avg_blocks, 
                    last_updated = CURRENT_TIMESTAMP;
            """
            executar_query(sql_def, (pid, nome, equipe, sigla, stl, blk, i+1))
            
        count_updated += 1

    log.info(f"✅ Rankings atualizados ({count_updated} atletas).")

if __name__ == "__main__":
    realizar_upsert_nba()