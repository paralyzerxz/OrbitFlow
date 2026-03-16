# main_pipeline.py
# ─────────────────────────────────────────────────────────────────────────────
# RESPONSABILIDADE: Orquestrador Global do Projeto OrbitFlow
#
# Este script amarra todas as etapas do processo (mineração, IA, publicação,
# download, edição e notificação via Telegram) e faz com que operem em ciclo
# contínuo, a cada 8 horas (set and forget).
# ─────────────────────────────────────────────────────────────────────────────

import os
import shutil
import time
import json
from datetime import datetime
import schedule # type: ignore

# Importa os módulos do pipeline
import time_manager # type: ignore
import miner # type: ignore
import transformer # type: ignore
import publisher_helper # type: ignore
import downloader # type: ignore
import editor # type: ignore
import notifier # type: ignore
import post_manager # type: ignore

# Diretório base do projeto para garantir caminhos absolutos corretos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def cleanup_workspace():
    """
    Limpa pastas e arquivos JSON temporários caso o vídeo seja recusado,
    para que o próximo ciclo de 8h comece do zero.
    """
    print("\n[Limpeza Padrão ADS] Iniciando faxina no workspace...")
    files_to_remove = ["raw_candidates.json", "transformed_videos.json"]
    
    for f in files_to_remove:
        path = os.path.join(BASE_DIR, f)
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"  - Deletado: {f}")
            except Exception as e:
                print(f"  [Erro] Falha ao deletar {f}: {e}")

    ready_dir = os.path.join(BASE_DIR, "ready_to_post")
    if os.path.exists(ready_dir):
        for item in os.listdir(ready_dir):
            # Preserva a pasta de dependencia IMAGEMAGICK 
            if item.upper() == "IMAGEMAGICK":
                continue
            
            item_path = os.path.join(ready_dir, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                print(f"  - Removido da pasta ready_to_post: {item}")
            except Exception as e:
                print(f"  [Erro] Não foi possível remover {item}: {e}")
                
    print("[Limpeza] Concluída.")


def run_pipeline():
    """
    Executa 1 ciclo fechado (Minerar -> IA -> Publisher -> Download -> Editar -> Aprovar).
    Retorna True se aprovado, False se falhou/recusado.
    """
    # 0. Limpeza Pragmática - Reseta o ambiente para evitar que arquivos velhos sujem a execução
    cleanup_workspace()
    
    # Consulta o Roteador ADS Global para saber a melhor janela atual (BRT)
    target_suggestion = time_manager.get_best_posting_target()
    
    print("\n" + "=" * 65)
    print(" 🚀 INICIANDO CICLO DO PIPELINE ORBITFLOW (GLOBAL 24/7)")
    print(f" 🎯 Rota Sugerida: {target_suggestion.replace('\n', ' ')}")
    print("=" * 65)
    
    # --- PASSO 1: Mineração ---
    print("\n---> PASSO 1: MINERAÇÃO")
    top_video_title = miner.mine()
    if not top_video_title:
        print("[Pipeline] Nenhum vídeo passou nos filtros. Abortando ciclo.")
        return False
        
    # --- PASSO 2: IA ---
    print("\n---> PASSO 2: TRANSFORMAÇÃO (IA GEMINI)")
    transformer.transform()
    
    # --- PASSO 3: Publisher ---
    print("\n---> PASSO 3: PUBLICAÇÃO (PACOTES)")
    publisher_helper.publish()
    
    # --- PASSO 4: Downloader ---
    print("\n---> PASSO 4: DOWNLOAD")
    downloader.download_all()
    
    # --- PASSO 5: Editor Visual ---
    print("\n---> PASSO 5: EDIÇÃO DE VÍDEO")
    json_ai_path = os.path.join(BASE_DIR, "transformed_videos.json")
    if not os.path.exists(json_ai_path):
        print("[Erro] transformed_videos.json sumiu inexplicavelmente. Abortando.")
        return False
        
    with open(json_ai_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if not data:
            return False
            
    # Extrai dados do pacote e descobre o slug gerado no sistema
    video_data = data[0]
    viral_title = video_data.get("title", "")
    original_title = video_data.get("original_title", "")
        
    # Recria lógica de slugify idêntica a do publisher_helper
    viral_title_safe = publisher_helper.build_viral_title(viral_title, original_title)
    slug = publisher_helper.slugify(viral_title_safe) or publisher_helper.slugify(original_title) or "untitled"
    
    video_folder = os.path.join(BASE_DIR, "ready_to_post", slug)
    video_basename = slug
    
    # Chama o Módulo de Edição e injeta o video_folder mapeado dinamicamente
    output_path = editor.main(video_folder=video_folder, video_basename=video_basename)
    if not output_path:
        print("[Erro] Falha ao injetar legendas no vídeo.")
        return False
        
    # --- PASSO 6: Aprovação Humana (Telegram) ---
    print("\n---> PASSO 6: APROVAÇÃO E TRAVA (TELEGRAM)")
    caption = f"Revisão Pendente (Aprovação Global): {viral_title_safe}"
    
    # Injeta o target_suggestion calculado no início do ciclo!
    is_approved = notifier.send_video_for_review(output_path, caption, target_suggestion)
    
    if is_approved:
        # --- PASSO 7: Horários e Agendamento Global ---
        print("\n---> PASSO 7: AGENDAMENTO DE UPLOAD")
        print(f"\n✅ VÍDEO APROVADO! O Pipeline irá priorizar a janela ideal:\n{target_suggestion}")
        
        # Redirecionamento de Armazenamento Permanente
        final_storage_dir = r"D:\Meus Projetos IDE\OrbitFlow\Shorts\ready_to_post\Videos and Shorts"
        os.makedirs(final_storage_dir, exist_ok=True)
        final_video_path = os.path.join(final_storage_dir, f"{video_basename}.mp4")
        try:
            shutil.move(output_path, final_video_path)
            print(f"\n[OK] Vídeo final movido permanentemente para:\n     {final_video_path}")
            
            # --- NOTIFICAÇÃO NATIVA (Watchdog) ---
            try:
                from plyer import notification # type: ignore
                notification.notify(
                    title="OrbitFlow: Vídeo Pronto!",
                    message=f"Vídeo aprovado e movido com sucesso:\n{video_basename}.mp4",
                    app_name="OrbitFlow",
                    timeout=10
                )
                print("     [Watchdog] Notificação nativa do Windows (Toast) disparada.")
            except ImportError:
                print("     [Aviso Watchdog] Plyer não instalado. Rode: pip install plyer para ver notificações nativas no Windows.")
            except Exception as e:
                print(f"     [Erro Watchdog] Falha ao enviar notificação do Windows: {e}")
                
            # --- INTEGRAÇÃO COM MÓDULO DE POSTAGEM ---
            try:
                post_manager.open_upload_environment(final_storage_dir)
            except Exception as e:
                print(f"     [Erro] Falha ao executar o Post Manager: {e}")
                
        except Exception as e:
            print(f"\n[Erro] Falha ao mover o vídeo para armazenamento: {e}")
            
        print("\n[OK] O upload foi encaminhado invisívelmente no background. (Mock)")
        return True
    else:
        print("\n---> ❌ VÍDEO RECUSADO NO TELEGRAM.")
        cleanup_workspace()
        return False


def main_loop():
    """
    Agendador contínuo usando a biblioteca 'schedule'.
    Configura o pipeline principal para rodar a cada 8 horas, 
    ou a cada 5 minutos em caso de falha na captação de vídeos.
    """
    print("\n[OrbitFlow] 🌐 Operação Global 24/7 Iniciada.")
    
    def job():
        success = False
        try:
            success = run_pipeline()
        except Exception as e:
            print(f"[ERRO CRÍTICO NO PIPELINE]: {e}")
        
        # Limpa o agendador atual para reprogramar com base no sucesso
        schedule.clear()
        if success:
            print(f"\n[Ciclo Concluído] Sucesso! A máquina entrará em dormência por 1 hora.")
            schedule.every(1).hours.do(job)
        else:
            print(f"\n[Ciclo Abortado] A operação falhou ou nenhum vídeo passou. Nova tentativa ágil em 2 minutos...")
            schedule.every(2).minutes.do(job)

    # Roda o primeiro ciclo imediatamente
    job()
    
    while True:
        schedule.run_pending()
        time.sleep(60) # Checa o agendamento a cada 1 minuto (seguro, leve na CPU)


if __name__ == "__main__":
    main_loop()
