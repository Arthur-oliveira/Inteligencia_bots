# services/fetch_nba.py
import pandas as pd
from datetime import datetime, timedelta
from nba_api.stats.endpoints import leaguedashteamstats, teamgamelog

def buscar_estatisticas_avancadas():
    """
    Busca estatísticas avançadas (Net Rating, Pace, eFG%) de todos os times na NBA API.
    Retorna um dicionário indexado pelo nome do time.
    """
    try:
        print("📊 [NBA API] Buscando Net Rating, Pace e eFG% da temporada 2024-25...")
        
        # measure_type_nullable='Advanced' traz NetRating, Pace, etc.
        stats = leaguedashteamstats.LeagueDashTeamStats(
            measure_type_nullable='Advanced',
            season='2024-25',
            per_mode_detailed='Per100Possessions' 
        )
        df = stats.get_data_frames()[0]
        
        # Cria um dicionário facilitador: { 'Los Angeles Lakers': { 'NET_RATING': 2.5, ... }, ... }
        stats_dict = {}
        for _, row in df.iterrows():
            team_name = row['TEAM_NAME']
            stats_dict[team_name] = {
                'NET_RATING': float(row['NET_RATING']), # Saldo de pontos a cada 100 posses
                'PACE': float(row['PACE']),             # Ritmo de jogo
                'EFG_PCT': float(row['EFG_PCT']),       # Aproveitamento de arremesso real
                'TEAM_ID': int(row['TEAM_ID'])
            }
        
        print(f"✅ [NBA API] Estatísticas de {len(stats_dict)} times carregadas.")
        return stats_dict

    except Exception as e:
        print(f"⚠️ [NBA API] Erro ao buscar stats: {e}")
        return {}

def verificar_back_to_back(team_name, stats_dict):
    """
    Verifica se o time jogou ontem (B2B) consultando o log de jogos oficial.
    """
    try:
        if team_name not in stats_dict:
            return False
            
        team_id = stats_dict[team_name]['TEAM_ID']
        
        # Busca os últimos jogos do time
        gamelog = teamgamelog.TeamGameLog(team_id=team_id, season='2024-25')
        df_log = gamelog.get_data_frames()[0]
        
        if df_log.empty:
            return False

        # Pega a data do último jogo registrado
        # A NBA API retorna strings como "OCT 25, 2024" ou ISO, pandas resolve.
        last_game_str = df_log.iloc[0]['GAME_DATE']
        last_game_date = pd.to_datetime(last_game_str).date()

        hoje = datetime.now().date()
        ontem = hoje - timedelta(days=1)
        
        # Se o último jogo foi ontem, é Back-to-Back
        return last_game_date == ontem

    except Exception as e:
        # Em caso de erro, assume False para não bloquear o bot
        print(f"⚠️ Erro B2B ({team_name}): {e}")
        return False