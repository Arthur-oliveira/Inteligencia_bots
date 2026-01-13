import time
from database.database_manager import log
from tips.data_refresher import realizar_upsert_nba
from tips.content_creator import gerar_agenda_simplificada, gerar_status_news, preparar_bilhete_free, gerar_choque_formatado
from tips.strategy_processor import analisar_confronto_estilos
from notifier_telegram import enviar_mensagem_telegram
from endpoints.api_handler import get_scoreboard

def buscar_jogos_nba():
    """Formata os jogos vindos da API."""
    eventos = get_scoreboard()
    return [{"id_casa": e['competitions'][0]['competitors'][0]['team']['id'],
             "nome_casa": e['competitions'][0]['competitors'][0]['team']['shortDisplayName'],
             "id_fora": e['competitions'][0]['competitors'][1]['team']['id'],
             "nome_fora": e['competitions'][0]['competitors'][1]['team']['shortDisplayName']} 
                for e in eventos]

def executar_producao():
    """Rotina principal de 1 hora."""
    log.info("🚀 Iniciando ciclo de produção NBA 2026...")
    
    # Atualiza banco com dados reais da temporada
    realizar_upsert_nba()
    
    jogos = buscar_jogos_nba()
    if not jogos:
        log.warning("📭 Sem jogos para hoje.")
        return

    # =========================================
    # FASE 1: Agenda e Status News
    # =========================================
    log.info("📢 Executando FASE 1: Agenda e Choques")
    enviar_mensagem_telegram(gerar_agenda_simplificada(jogos))
    time.sleep(3)
    enviar_mensagem_telegram(gerar_status_news(jogos))
    
    # Intervalo entre fases (Ex: 1 hora na produção, aqui reduzido para teste se necessário)
    log.info("⏳ Aguardando intervalo entre fases...")
    time.sleep(10) 
    
    # =========================================
    # FASE 2: Choques de Estilos (Prioridade)
    # =========================================
    log.info("🚨 Executando FASE 2 - Parte A: Choques de Estilos")
    for jogo in jogos:
        is_choque, time_vant = analisar_confronto_estilos(jogo['nome_casa'], jogo['nome_fora'])
        if is_choque:
            # Define quem é o rival baseado em quem tem a vantagem
            rival = jogo['nome_fora'] if time_vant == jogo['nome_casa'] else jogo['nome_casa']
            mensagem_choque = gerar_choque_formatado(time_vant, rival)
            enviar_mensagem_telegram(mensagem_choque)
            time.sleep(3) # Pausa leve para não floodar a API do Telegram

    # =========================================
    # FASE 3: Bilhetes Free (Após os Choques)
    # =========================================
    log.info("🎫 Executando FASE 2 - Parte B: Bilhetes Free")
    for jogo in jogos:
        bilhete = preparar_bilhete_free(jogo)
        # Só envia se o bilhete foi gerado (ou seja, se atingiu os critérios)
        if bilhete:
            enviar_mensagem_telegram(bilhete)
            time.sleep(5)

if __name__ == "__main__":
    while True:
        try:
            executar_producao()
            log.info("💤 Ciclo concluído. Próxima execução em 1 hora.")
            time.sleep(3600)
        except Exception as e:
            log.error(f"Erro fatal: {e}")
            time.sleep(300)