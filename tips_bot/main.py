import time
import schedule
from datetime import datetime, timedelta
from database.database_manager import log
from tips.data_refresher import realizar_upsert_nba
from tips.content_creator import (
    gerar_agenda_simplificada, 
    gerar_status_news, 
    preparar_bilhete_free, 
    gerar_choque_formatado
)
from tips.strategy_processor import analisar_confronto_estilos
from notifier_telegram import enviar_mensagem_telegram
from endpoints.api_handler import get_scoreboard

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def buscar_jogos_nba():
    """
    Formata os jogos vindos da API e converte horário para Brasília (UTC-3).
    BLINDAGEM: Suporta formatos com/sem segundos e milissegundos.
    """
    try:
        eventos = get_scoreboard()
        if not eventos:
            return []
            
        jogos_formatados = []
        
        for e in eventos:
            horario_formatado = "--:--"
            date_str = "N/A"
            
            # Tratamento de Horário (Conversão UTC -> Brasília)
            try:
                # Tenta pegar a data na raiz ou na competição
                date_str = e.get('date') or e['competitions'][0].get('date')
                
                # Lista de formatos possíveis da API da ESPN
                formatos_possiveis = [
                    "%Y-%m-%dT%H:%M:%SZ",       # Padrão 1 (Com segundos)
                    "%Y-%m-%dT%H:%M:%S.%fZ",    # Padrão 2 (Com millis)
                    "%Y-%m-%dT%H:%MZ"           # Padrão 3 (SEM segundos)
                ]
                
                data_utc = None
                for fmt in formatos_possiveis:
                    try:
                        data_utc = datetime.strptime(date_str, fmt)
                        break 
                    except ValueError:
                        continue 
                
                if data_utc:
                    # Subtrai 3 horas (Fuso Brasília)
                    data_br = data_utc - timedelta(hours=3)
                    horario_formatado = data_br.strftime("%H:%M")
                else:
                    log.warning(f"⚠️ Formato de data desconhecido recebido da API: {date_str}")

            except Exception as erro_data:
                log.error(f"Erro ao processar data ({date_str}): {erro_data}")
                horario_formatado = "--:--"

            jogos_formatados.append({
                "id_casa": e['competitions'][0]['competitors'][0]['team']['id'],
                "nome_casa": e['competitions'][0]['competitors'][0]['team']['shortDisplayName'],
                "id_fora": e['competitions'][0]['competitors'][1]['team']['id'],
                "nome_fora": e['competitions'][0]['competitors'][1]['team']['shortDisplayName'],
                "horario": horario_formatado
            })
            
        return jogos_formatados

    except Exception as e:
        log.error(f"Erro ao buscar jogos: {e}")
        return []

# ==============================================================================
# TAREFAS AGENDADAS (JOBS)
# ==============================================================================

def job_atualizar_dados():
    """Tarefa 1: Executada de 1 em 1 hora."""
    log.info("🔄 [JOB] Iniciando atualização de dados frescos (Banco de Dados)...")
    realizar_upsert_nba()
    log.info("✅ [FIM] Atualização de dados concluída. Voltando ao loop...")

def job_fase_1_tarde():
    """Tarefa 2: Executada (Agenda + Status News)."""
    log.info("📢 [JOB] Executando FASE 1: Envio da Tarde (Agenda + Status)...")
    
    jogos = buscar_jogos_nba()
    if not jogos:
        log.warning("📭 Sem jogos encontrados para a Fase 1.")
        log.info("✅ [FIM] FASE 1 finalizada (sem jogos). Voltando ao loop...")
        return

    # 1. Envia Agenda
    try:
        enviar_mensagem_telegram(gerar_agenda_simplificada(jogos))
        time.sleep(3) 
        
        # 2. Envia Status News
        enviar_mensagem_telegram(gerar_status_news(jogos))
        
        # LOG DE CONCLUSÃO ADICIONADO
        log.info("✅ [FIM] FASE 1 concluída com sucesso. Aguardando próximo agendamento...")
        
    except Exception as e:
        log.error(f"Erro na Fase 1: {e}")

def job_fase_2_final():
    """Tarefa 3: Executada (Choque + Bilhetes)."""
    log.info("🎫 [JOB] Executando FASE 2: Análise Final (Choques + Bilhetes)...")
    
    jogos = buscar_jogos_nba()
    if not jogos:
        log.warning("📭 Sem jogos encontrados para a Fase 2.")
        log.info("✅ [FIM] FASE 2 finalizada (sem jogos). Voltando ao loop...")
        return

    # Parte A: Choques de Estilos
    log.info("🚨 Verificando Choques de Estilos...")
    for jogo in jogos:
        try:
            is_choque, time_vant = analisar_confronto_estilos(jogo['nome_casa'], jogo['nome_fora'])
            if is_choque:
                rival = jogo['nome_fora'] if time_vant == jogo['nome_casa'] else jogo['nome_casa']
                mensagem_choque = gerar_choque_formatado(time_vant, rival)
                enviar_mensagem_telegram(mensagem_choque)
                time.sleep(5)
        except Exception as e:
            log.error(f"Erro ao processar choque para {jogo['nome_casa']} x {jogo['nome_fora']}: {e}")

    # Parte B: Bilhetes Free
    log.info("🎫 Gerando Bilhetes Free...")
    for jogo in jogos:
        try:
            bilhete = preparar_bilhete_free(jogo)
            if bilhete:
                enviar_mensagem_telegram(bilhete)
                time.sleep(5)
        except Exception as e:
            log.error(f"Erro ao processar bilhete para {jogo['nome_casa']} x {jogo['nome_fora']}: {e}")
            
    # LOG DE CONCLUSÃO ADICIONADO
    log.info("✅ [FIM] FASE 2 concluída com sucesso. Aguardando próximo agendamento...")

# ==============================================================================
# CONTROLE DO LOOP PRINCIPAL
# ==============================================================================

def main_loop_control():
    """
    Função de controle do loop principal com MODO DIAGNÓSTICO.
    """
    log.info("=========================================================")
    log.info("🚀 INICIALIZANDO O AUTOMATIZADOR DO BOT NBA 24/7")
    log.info("=========================================================")

    # -----------------------------------------------------------
    # CONFIGURAÇÃO DE HORÁRIOS
    # -----------------------------------------------------------
    
    # 1ª: De uma em uma hora, busca dados frescos
    schedule.every(1).hours.do(job_atualizar_dados)
    
    # 2ª: FASE 1 (Agenda + Status News)
    # Defina aqui o horário oficial ou de teste (Ex: "15:30")
    schedule.every().day.at("22:32").do(job_fase_1_tarde)
    
    # 3ª: FASE 2 (Choque + Bilhete)
    # Defina aqui o horário oficial ou de teste (Ex: "16:30")
    schedule.every().day.at("22:33").do(job_fase_2_final)

    # Executa uma atualização imediata ao ligar o bot para garantir dados
    log.info("⚡ Executando atualização inicial de dados...")
    job_atualizar_dados()

    # --- DIAGNÓSTICO DE AGENDAMENTO ---
    log.info("=========================================================")
    log.info("📅 [DIAGNÓSTICO] VERIFICANDO MEMÓRIA DE AGENDAMENTOS:")
    log.info(f"📆 Hora do Sistema: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    jobs = schedule.get_jobs()
    if not jobs:
        log.warning("⚠️ ALERTA: Nenhuma tarefa foi agendada! Verifique o código.")
    
    for i, job in enumerate(jobs):
        log.info(f"   [{i+1}] Próxima execução: {job.next_run} | Tarefa: {job.job_func.__name__}")
        
    log.info("=========================================================")
    log.info(f"✅ Loop iniciado. Verificando relógio a cada 1 segundo...")
    
    while True:
        try:
            # Verifica se há tarefas agendadas para rodar agora
            schedule.run_pending()
            
            # Sleep de 1 segundo para precisão exata
            time.sleep(1)
            
        except KeyboardInterrupt:
            log.warning("\nProcesso interrompido pelo usuário.")
            break
        except Exception as e:
            log.error(f"\nERRO FATAL NO LOOP: {e}. Reiniciando ciclo em 1 minuto...")
            time.sleep(60)

if __name__ == "__main__":
    main_loop_control()