# notifier.py
# ─────────────────────────────────────────────────────────────────────────────
# RESPONSABILIDADE: Etapa 6 do pipeline — Revisão via Telegram.
#
# Este script atua como a interface de comunicação entre o pipeline e o 
# usuário via Telegram API. Ele envia o vídeo renderizado para o celular 
# do usuário, junto com botões interativos (Inline Keyboards) para aprovação 
# ou recusa do conteúdo.
#
# POR QUE ISSO É IMPORTANTE (Padrão ADS)?
# Essa interação entre o Bot e o Algoritmo garante que o Passo 7 (Postagem)
# só aconteça SOMENTE APÓS a autorização explícita humana. O script paralisa
# a execução e fica "escutando" as respostas via webhook/polling do Telegram. 
# Se recusado, o vídeo pode ser descartado. Se aprovado, o fluxo segue livre.
# ─────────────────────────────────────────────────────────────────────────────

import os
import time
import requests # type: ignore
import json # type: ignore
import notifier # type: ignore

# =============================================================================
# CREDENCIAIS DO TELEGRAM
# -----------------------------------------------------------------------------
# Substitua o CHAT_ID pelo seu ID pessoal do Telegram. 
# Para encontrar seu ID, mande uma mensagem para o bot @userinfobot no Telegram.
# =============================================================================
TOKEN = "8684867832:AAF9c9B1STt3KFmaBnC-ARxxv3bDwJvxsBw"
CHAT_ID = "5980334867"  # <-- PREENCHA COM SEU CHAT ID AQUI
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


def wait_for_user_decision(message_id: int, video_path: str) -> bool:
    """
    Fica em um loop contínuo (polling) escutando os cliques nos botões do Telegram.
    Retorna True se aprovado, ou False se recusado e deletado.
    """
    offset = None
    print("\n[Telegram] Aguardando sua decisão no celular...")

    while True:
        url = f"{BASE_URL}/getUpdates"
        # Define o dicionário explicitamente para evitar erros de tipagem do Pyright
        params: dict = {"timeout": 10}
        # Telegram pede que allowed_updates seja string JSON quando passado por Query Parameter
        params["allowed_updates"] = json.dumps(["callback_query"])
        
        if offset:
            params["offset"] = offset

        try:
            resp = requests.get(url, params=params).json()
            
            for update in resp.get("result", []):
                # Atualiza o offset para não ler a mesma mensagem na próxima volta
                offset = update["update_id"] + 1
                
                if "callback_query" in update:
                    cq = update["callback_query"]
                    data = cq["data"]
                    cq_id = cq["id"]
                    
                    # 1) Avisa o Telegram que recebemos o clique (tira o ícone de relógio no botão)
                    requests.post(f"{BASE_URL}/answerCallbackQuery", json={"callback_query_id": cq_id})
                    
                    # 2) Processa a ação baseada no botão clicado
                    if data == "accept":
                        # Substitui os botões vazios para evitar múltiplos cliques
                        requests.post(f"{BASE_URL}/editMessageReplyMarkup", json={
                            "chat_id": str(CHAT_ID), 
                            "message_id": message_id, 
                            "reply_markup": {"inline_keyboard": []}
                        })
                        requests.post(f"{BASE_URL}/sendMessage", json={
                            "chat_id": str(CHAT_ID), 
                            "text": "✅ Vídeo ACEITO! Avançando no pipeline..."
                        })
                        print("[Telegram] ✔ Vídeo APROVADO pelo usuário!")
                        return True
                        
                    elif data == "reject":
                        # Exibe nova mensagem de confirmação para a recusa
                        new_kb = {
                            "inline_keyboard": [
                                [{"text": "Sim, tenho", "callback_data": "confirm_reject"}, 
                                 {"text": "Cancelar", "callback_data": "cancel_reject"}]
                            ]
                        }
                        requests.post(f"{BASE_URL}/sendMessage", json={
                            "chat_id": str(CHAT_ID),
                            "text": "Você tem certeza que quer recusar?",
                            "reply_to_message_id": message_id,
                            "reply_markup": new_kb
                        })
                        
                    elif data == "confirm_reject":
                        # Editamos a mensagem de confirmação para informar do encerramento
                        if "message" in cq:
                            confirmation_msg_id = cq["message"]["message_id"]
                            requests.post(f"{BASE_URL}/editMessageText", json={
                                "chat_id": str(CHAT_ID), 
                                "message_id": confirmation_msg_id, 
                                "text": "🗑️ Vídeo recusado e processo encerrado."
                            })
                        print("\n[Telegram] ❌ Vídeo RECUSADO pelo usuário.")
                        print(f"[Log] Tentando deletar arquivo rejeitado: {video_path}")
                        
                        # Tenta deletar o arquivo de forma segura
                        try:
                            if os.path.exists(video_path):
                                os.remove(video_path)
                                print("[Log] -> Arquivo de vídeo final excluído com sucesso do disco.")
                        except Exception as e:
                            print(f"[Log] -> Erro ao excluir o arquivo: {e}")
                            
                        return False
                        
                    elif data == "cancel_reject":
                        # Desfaz a intenção de recusar. Tira os botões e avisa no chat
                        if "message" in cq:
                            confirmation_msg_id = cq["message"]["message_id"]
                            requests.post(f"{BASE_URL}/editMessageReplyMarkup", json={
                                "chat_id": str(CHAT_ID), 
                                "message_id": confirmation_msg_id, 
                                "reply_markup": {"inline_keyboard": []}
                            })
                        
                        requests.post(f"{BASE_URL}/sendMessage", json={
                            "chat_id": str(CHAT_ID), 
                            "text": "Cancelado. Use os botões originais no vídeo acima para aprovar ou recusar."
                        })
                        
        except Exception as e:
            # Em caso de instabilidade pontual, loga e continua o loop
            print(f"[Telegram] Erro na comunicação de rede: {e}")
            
        # Espera um pouco antes do próximo request
        time.sleep(2)
        
    return False # Retorno de segurança caso o loop quebre



def send_video_for_review(video_path: str, caption: str, target_suggestion: str = "") -> bool:
    """
    Usa a biblioteca requests para enviar o vídeo .mp4 finalizado ao usuário
    com uma legenda e botões iniciais Inline Keyboards.
    
    O target_suggestion é adicionado à legenda para indicar o melhor país.
    """
    if not CHAT_ID:
        print("\n[Aviso] Variável CHAT_ID vazia. Para testar o Telegram, preencha no notifier.py!")
        return True # Segue o baile para não travar quem testa sem telegram

    print(f"\n[Telegram] Fazendo upload de '{os.path.basename(video_path)}' para sua aprovação...")
    
    # Dicionário do Inline Keyboard inicial (Aceitar / Recusar)
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Aceitar", "callback_data": "accept"},
                {"text": "❌ Recusar", "callback_data": "reject"}
            ]
        ]
    }
    
    # Adiciona a sugestão de roteamento ao caption apenas se fornecido
    final_caption = f"{caption}\n\n🎯 Rota Sugerida:\n{target_suggestion}" if target_suggestion else caption
    
    url = f"{BASE_URL}/sendVideo"
    data = {
        "chat_id": str(CHAT_ID),
        "caption": final_caption,
        "reply_markup": json.dumps(keyboard)
    }
    
    try:
        # Abre o arquivo de vídeo como leitura binária para envio multipart
        with open(video_path, "rb") as video_file:
            files = {"video": video_file}
            response = requests.post(url, data=data, files=files).json()
            
        if not response.get("ok"):
            print(f"[Telegram] Falha ao enviar vídeo: {response.get('description')}")
            return False
            
        # Extrai a ID da mensagem de vídeo para referenciá-la nas respostas
        message_id = response["result"]["message_id"]
        
        # Chama o loop de polling para aguardar a decisão humana
        return wait_for_user_decision(message_id, video_path)
        
    except Exception as e:
        print(f"[Telegram] Erro crítico ao conectar com api.telegram.org: {e}")
        return False


# =============================================================================
# BLOCO DE EXECUÇÃO DE TESTE (Validação do Passo 6)
# -----------------------------------------------------------------------------
# Explicação ADS (Análise e Desenvolvimento de Sistemas):
# Este bloco 'if __name__ == "__main__":' garante o conceito de Modularização.
# Ele só será executado se você rodar este script (notifier.py) DIRETAMENTE 
# pelo terminal ou IDE. Se outro script (como o editor.py) fizer o 'import'
# deste arquivo para usar suas funções, todo este bloco de teste será IGNORADO.
# Isso permite testar módulos de forma isolada sem afetar o sistema principal.
# =============================================================================
if __name__ == "__main__":
    # Caminho absoluto do vídeo de teste já renderizado
    video_teste_path = r"D:\Meus Projetos IDE\OrbitFlow\Shorts\ready_to_post\you_wont_believe_these_5_life_hacks_are_real\final_video.mp4"
    
    # Título/Legenda enviada junto com o vídeo no Telegram
    titulo_teste = "🧪 TESTE DE INTEGRAÇÃO (Passo 6): Validando revisão de vídeo via Telegram."
    
    print("\n=======================================================")
    print(" INICIANDO TESTE ISOLADO DO MÓDULO DE NOTIFICAÇÃO")
    print("=======================================================")
    
    # Chama a função principal de envio passando o caminho e a legenda
    resultado = send_video_for_review(video_path=video_teste_path, caption=titulo_teste)
    
    if resultado:
        print("\n[Resultado do Teste] O vídeo foi APROVADO com sucesso no teste isolado!")
    else:
        print("\n[Resultado do Teste] O vídeo foi RECUSADO ou abortado (comportamento manipulado com sucesso).")
