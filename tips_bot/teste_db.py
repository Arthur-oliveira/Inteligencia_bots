from database.database_manager import executar_query, log

def teste_rapido():
    log.info("🧪 Iniciando teste de injeção manual...")
    sql = """
        INSERT INTO league_offensive_rankings 
        (player_name, team, team_abbreviation, avg_points, three_point_pct, rank_position)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (player_name) DO UPDATE SET last_updated = CURRENT_TIMESTAMP;
    """
    sucesso = executar_query(sql, ("TESTE LUKA", "Lakers", "LAL", 33.5, 31.9, 1))
    
    if sucesso:
        print("✅ SUCESSO! O banco recebeu o dado de teste.")
    else:
        print("❌ FALHA! Verifique os logs na pasta /log.")

if __name__ == "__main__":
    teste_rapido()