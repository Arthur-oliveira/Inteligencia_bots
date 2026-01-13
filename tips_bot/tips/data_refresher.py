from database.database_manager import log, executar_query
from endpoints.api_handler import get_league_rankings

def realizar_upsert_nba():
    """Alimenta o banco com dados reais da temporada atual."""
    log.info("🔄 Sincronizando dados reais da temporada 2025/26...")
    atletas = get_league_rankings()
    
    if not atletas:
        log.warning("⚠️ Nenhum dado recebido da ESPN.")
        return

    for i, item in enumerate(atletas):
        atleta = item.get('athlete', {})
        nome = atleta.get('displayName')
        equipe = atleta.get('teamName', 'N/A')
        sigla = atleta.get('teamShortName', 'N/A')

        # Dados Ofensivos
        off = next((c['totals'] for c in item['categories'] if c['name'] == 'offensive'), [])
        if off:
            ppg, t_pct = float(off[0]), float(off[6])
            sql_off = """
                INSERT INTO league_offensive_rankings (player_name, team, team_abbreviation, avg_points, three_point_pct, rank_position)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_name) DO UPDATE SET 
                    avg_points = EXCLUDED.avg_points, rank_position = EXCLUDED.rank_position, last_updated = CURRENT_TIMESTAMP;
            """
            executar_query(sql_off, (nome, equipe, sigla, ppg, t_pct, i+1))

        # Dados Defensivos
        defen = next((c['totals'] for c in item['categories'] if c['name'] == 'defensive'), [])
        if defen:
            stl, blk = float(defen[0]), float(defen[1])
            sql_def = """
                INSERT INTO league_defensive_rankings (player_name, team, team_abbreviation, avg_steals, avg_blocks, rank_position)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_name) DO UPDATE SET 
                    avg_steals = EXCLUDED.avg_steals, avg_blocks = EXCLUDED.avg_blocks, last_updated = CURRENT_TIMESTAMP;
            """
            executar_query(sql_def, (nome, equipe, sigla, stl, blk, i+1))

    log.info(f"✅ Banco de dados atualizado com {len(atletas)} atletas.")

if __name__ == "__main__":
    realizar_upsert_nba()