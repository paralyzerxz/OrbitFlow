# time_manager.py
# ─────────────────────────────────────────────────────────────────────────────
# RESPONSABILIDADE: Roteamento de postagem baseado em fusos horários globais.
#
# Calcula a melhor região do mundo para postagem de um Short baseado no horário
# atual do servidor (convertido para BRT - Brasília Time).
#
# LÓGICA DE JANELAS DE PICO (Horário de Brasília):
#   - 05:00 às 08:00 -> Oceania (Austrália/Nova Zelândia)
#   - 14:00 às 17:00 -> Europa (UK/Norte da Europa)
#   - 20:00 às 23:00 -> América do Norte (EUA/Canadá)
#
# Se o disparo ocorrer fora dessas janelas, o roteador fará um fallback
# estratégico sugerindo o agendamento para o mercado norte-americano.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime
import pytz # type: ignore

def get_best_posting_target() -> str:
    """
    Analisa a hora atual (BRT) e retorna uma string pré-formatada informando
    a melhor região para postar o viral.
    """
    # Define o fuso horário de referência (Brasília)
    tz_brt = pytz.timezone('America/Sao_Paulo')
    
    # Obtém a hora atual exata neste fuso
    now_brt = datetime.now(tz_brt)
    hour = now_brt.hour

    # --- Lógica do Roteador Numérico ---
    if 5 <= hour < 8:
        target = "🦘 Oceania (Austrália e Nova Zelândia)\n👉 (Horário de Pico local)"
        
    elif 14 <= hour < 17:
        target = "🇬🇧 Europa (Reino Unido e Norte Europeu)\n👉 (Horário de Pico local)"
        
    elif 20 <= hour < 23:
        target = "🇺🇸 América do Norte (EUA e Canadá)\n👉 (Horário de Pico local)"
        
    else:
        # Fallback para o horário comercial norte-americano ou sugestão de pausa
        target = "🇺🇸 EUA/CA (Fora da janela de pico ideal. Considere postar/agendar entre 20h-23h BRT)"

    return target

if __name__ == "__main__":
    # Teste unitário simples
    print("Módulo Time Manager")
    print("-" * 20)
    print(f"Sugestão Atual: \n{get_best_posting_target()}")
