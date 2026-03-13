# downloader.py
# ─────────────────────────────────────────────────────────────────────────────
# RESPONSABILIDADE: Etapa 4 do pipeline — download físico dos vídeos.
#
# Lê a lista de candidatos em raw_candidates.json (gerada pelo miner.py) e
# baixa cada vídeo usando a biblioteca yt-dlp, salvando-os organizados dentro
# da pasta ready_to_post/ com um nome de arquivo limpo e previsível.
#
# FLUXO:
#   download_all() → download_video() → ready_to_post/<slug>/<slug>.mp4
#
# IMPORTANTE: O nome do arquivo gerado aqui deve coincidir com o campo
#   'suggested_filename' gerado pelo publisher_helper.py, para que o pacote
#   de publicação aponte para o arquivo correto.
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
import re
import unicodedata
import yt_dlp  # type: ignore


# ─── Configuração ─────────────────────────────────────────────────────────────

# Arquivo de entrada: gerado pelo miner.py
INPUT_FILE: str = "raw_candidates.json"

# Pasta raiz onde os vídeos serão salvos
OUTPUT_DIR: str = "ready_to_post"


# ─── Utilitários ──────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """
    Converte um título em um slug seguro para usar como nome de pasta/arquivo.
    Exemplo: "Iran, Israel & America!" → "iran_israel__america"
    
    Essa função é idêntica à do publisher_helper.py para garantir que o nome
    do arquivo baixado seja sempre o mesmo nome esperado pelo pacote de publicação.
    """
    # 1. Remove acentos e caracteres Unicode especiais
    normalized: str = unicodedata.normalize("NFD", str(text))
    ascii_text: str = normalized.encode("ascii", "ignore").decode("ascii")

    # 2. Remove tudo que não for letras, números ou espaços
    clean: str = re.sub(r"[^a-zA-Z0-9\s]", "", ascii_text)

    # 3. Troca espaços por underscores e coloca em minúsculo
    slug_tmp: str = re.sub(r"\s+", "_", clean.strip()).lower()

    # 4. Trunca em 60 caracteres de forma segura, sem usar fatiamento [:]
    chars: list[str] = []
    for char in str(slug_tmp):
        if len(chars) < 60:
            chars.append(char)

    return str("".join(chars))


def load_candidates() -> list[dict]:
    """
    Abre o raw_candidates.json e retorna a lista de vídeos para baixar.
    Retorna uma lista vazia se o arquivo não existir ou estiver corrompido.
    """
    if not os.path.exists(INPUT_FILE):
        print(f"[ERRO] Arquivo '{INPUT_FILE}' não encontrado. Execute o miner.py primeiro.")
        return []

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Garante que o retorno é sempre uma lista de dicionários
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
            return []
    except Exception as e:
        print(f"[ERRO] Falha ao ler '{INPUT_FILE}': {e}")
        return []


# ─── Download ─────────────────────────────────────────────────────────────────

def download_video(title: str, url: str) -> None:
    """
    Baixa um único vídeo usando yt-dlp e o salva na pasta correta.

    Parâmetros do yt-dlp explicados:
      - format: Define a qualidade do vídeo a baixar.
          'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
          Tenta primeiro o melhor vídeo MP4 + melhor áudio M4A;
          se não achar, pega o melhor formato MP4 disponível;
          se ainda assim não achar, pega o melhor que tiver.

      - outtmpl: Template do caminho e nome do arquivo de saída (Output Template).
          Usamos o nosso próprio slug no lugar de %(title)s para garantir
          que o nome do arquivo seja limpo, sem caracteres especiais,
          e idêntico ao 'suggested_filename' gerado pelo publisher_helper.py.

      - quiet: True → suprime o output verboso do yt-dlp no terminal.

      - no_warnings: True → esconde avisos técnicos que poluem o terminal.

      - ignoreerrors: True → se um vídeo falhar, o programa continua em vez
          de travar. Essencial para rodar um loop sem intervenção manual.
    """
    slug: str = slugify(title)

    # Cria uma subpasta exclusiva para este vídeo dentro de ready_to_post/
    # Exemplo: ready_to_post/iran_israel_america/
    video_dir: str = os.path.join(OUTPUT_DIR, slug)
    os.makedirs(video_dir, exist_ok=True)

    # Caminho completo onde o arquivo .mp4 será salvo
    # Exemplo: ready_to_post/iran_israel_america/iran_israel_america.mp4
    output_path: str = os.path.join(video_dir, f"{slug}.mp4")

    # ── Verificação: pula o download se o arquivo já existir ──────────────────
    if os.path.exists(output_path):
        print(f"  [PULANDO] Arquivo já existe: {output_path}")
        return

    # ── Configuração do yt-dlp ────────────────────────────────────────────────
    ydl_opts: dict = {
        # Tenta MP4 com melhor qualidade; fallback para o melhor formato disponível
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",

        # outtmpl: caminho exato onde o arquivo será salvo.
        # Usamos o nosso slug para ter um nome limpo e previsível.
        # O yt-dlp adiciona a extensão correta (.mp4) automaticamente.
        "outtmpl": os.path.join(video_dir, f"{slug}.%(ext)s"),

        # Modo silencioso — sem barra de progresso ou logs técnicos
        "quiet": True,

        # Ignora avisos como cookies expirados ou restrições de região
        "no_warnings": True,

        # Continua para o próximo vídeo em caso de erro, sem travar o loop
        "ignoreerrors": True,
    }

    # ── Download ──────────────────────────────────────────────────────────────
    try:
        print(f"  [BAIXANDO] {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"  [OK] Salvo em: {output_path}")
    except Exception as e:
        print(f"  [ERRO] Falha ao baixar '{title}': {e}")


# ─── Orquestrador Principal ───────────────────────────────────────────────────

def download_all() -> None:
    """
    Lê todos os candidatos do raw_candidates.json e baixa cada um deles.
    Vídeos já baixados são pulados automaticamente para economizar banda.
    """
    # Garante que a pasta de destino raiz existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    videos: list[dict] = load_candidates()

    if not videos:
        print("[INFO] Nenhum vídeo para baixar.")
        return

    total: int = len(videos)
    print(f"[INFO] {total} vídeo(s) encontrado(s) em '{INPUT_FILE}'. Iniciando downloads...\n")

    # Loop simples pelos vídeos — cada um é tratado de forma independente
    for i, video in enumerate(videos, start=1):
        title: str = str(video.get("title", f"video_{i}")).strip()
        url: str = str(video.get("url", "")).strip()

        print(f"[{i}/{total}] {title}")

        # Verifica se a URL está presente antes de tentar baixar
        if not url:
            print(f"  [AVISO] URL ausente para este vídeo. Pulando.")
            continue

        download_video(title=title, url=url)

    print(f"\n[OK] Downloads concluídos. Vídeos disponíveis em '/{OUTPUT_DIR}/'. 🎬")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    download_all()
