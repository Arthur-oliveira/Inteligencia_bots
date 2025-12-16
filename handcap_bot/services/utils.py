# services/utils.py

def normalizar_nome_time(nome_espn):
    """
    Traduz nomes da ESPN para o padrão da NBA API.
    """
    # Mapa de tradução (ESPN -> NBA API)
    mapa_nomes = {
        "LA Clippers": "L.A. Clippers",
        "Los Angeles Clippers": "L.A. Clippers",
        "Philadelphia 76ers": "Philadelphia 76ers",
        # Adicione outros se notar erro, mas geralmente esses são os principais diferentes
    }
    
    # Retorna o nome traduzido ou o original se não estiver no mapa
    return mapa_nomes.get(nome_espn, nome_espn)