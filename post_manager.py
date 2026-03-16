import os
import webbrowser
import subprocess

def open_upload_environment(video_folder: str = ""):
    """
    Abre o ambiente completo para o postador:
    1. A pasta onde estão os shorts finais aprovados.
    2. O YouTube Studio para Upload.
    3. O TikTok Creator Center para Upload.
    """
    print("\n[Post Manager] Preparando o ecossistema de postagem...")

    # 1. Abre a Pasta Mestra no Windows Explorer
    if os.path.exists(video_folder):
        print(f"  -> Abrindo pasta final: {video_folder}")
        if os.name == 'nt': # Verifica se é Windows
            os.startfile(video_folder) # type: ignore
        else:
            subprocess.Popen(['explorer', video_folder])
    else:
        print(f"  [Erro] Pasta '{video_folder}' não encontrada.")
    
    # 2. Abre as URLs (Use o navegador padrão do Windows)
    youtube_upload_url = "https://studio.youtube.com/channel/UC/videos/upload?d=sq"
    tiktok_upload_url = "https://www.tiktok.com/creator-center/upload"
    
    try:
        print("  -> Abrindo YouTube Studio...")
        webbrowser.open_new_tab(youtube_upload_url)
        
        print("  -> Abrindo TikTok Creator Center...")
        webbrowser.open_new_tab(tiktok_upload_url)
    except Exception as e:
        print(f"  [Erro] Falha ao abrir navegador: {e}")
        
    print("[Post Manager] Ambiente pronto. É só arrastar e soltar e colar o texto!")

if __name__ == "__main__":
    test_folder = r"D:\Meus Projetos IDE\OrbitFlow\Shorts\ready_to_post\Videos and Shorts"
    open_upload_environment(test_folder)
