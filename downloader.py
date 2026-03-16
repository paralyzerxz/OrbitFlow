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

# Arquivo de entrada: gerado pelo transformer.py com os vídeos e metadados IA
INPUT_FILE: str = "transformed_videos.json"

# Pasta raiz onde os vídeos serão salvos, um por subpasta
OUTPUT_DIR: str = "ready_to_post"


# ─── Utilitários ──────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """
    Converte um título em um slug seguro para usar como nome de pasta/arquivo.
    Exemplo: "Iran, Israel & America!" → "iran_israel_america"

    Esta função é idêntica à do publisher_helper.py para garantir que o nome
    do arquivo baixado seja sempre o mesmo nome esperado pelo pacote de publicação.

    Passos:
      1. Remove acentos (é → e, ç → c, etc.)
      2. Remove tudo que não seja letra, número ou espaço
      3. Substitui espaços por underscores e coloca em minúsculo
      4. Limita a 60 caracteres para manter nomes de arquivo razoáveis
    """
    # Passo 1: normaliza Unicode e remove acentos
    normalized: str = unicodedata.normalize("NFD", str(text))
    ascii_text: str = normalized.encode("ascii", "ignore").decode("ascii")

    # Passo 2: remove características especiais (pontuação, símbolos, etc.)
    clean: str = re.sub(r"[^a-zA-Z0-9\s]", "", ascii_text)

    # Passo 3: espaços → underscores, tudo minúsculo
    slug_tmp: str = re.sub(r"\s+", "_", clean.strip()).lower()

    # Passo 4: trunca em 60 caracteres sem usar fatiamento [:] (evita erro de tipagem)
    chars: list[str] = []
    for char in str(slug_tmp):
        if len(chars) < 60:
            chars.append(char)

    return str("".join(chars))


def load_candidates() -> list[dict]:
    """
    Abre o raw_candidates.json e retorna a lista de vídeos para baixar.
    Retorna uma lista vazia se o arquivo não existir ou estiver corrompido,
    sem travar o programa — o usuário verá uma mensagem explicativa.
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
    Baixa um único vídeo do YouTube usando yt-dlp e o salva na subpasta correta.

    Organização dos arquivos:
      ready_to_post/
        iran_israel_america/            ← subpasta criada automaticamente
          iran_israel_america.mp4       ← vídeo baixado

    Parâmetros do yt-dlp explicados:
      - format:
          'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
          Tenta primeiro o melhor vídeo MP4 + melhor áudio M4A.
          Se não achar, pega o melhor MP4 disponível.
          Se ainda assim não achar, pega o melhor formato que existir.

      - outtmpl:
          Template do caminho de saída (Output Template).
          Usamos o nosso próprio slug para garantir nomes limpos e previsíveis,
          iguais ao campo 'suggested_filename' do publisher_helper.py.

      - quiet: suprime o output verboso do yt-dlp no terminal.

      - no_warnings: esconde avisos técnicos (cookies, região, etc.).

      - ignoreerrors: se um vídeo falhar, o loop continua sem travar.
    """
    # Converte o título em um nome de pasta/arquivo seguro
    slug: str = slugify(title)

    # Cria a subpasta exclusiva para este vídeo dentro de ready_to_post/
    video_dir: str = os.path.join(OUTPUT_DIR, slug)
    os.makedirs(video_dir, exist_ok=True)  # exist_ok=True: não dá erro se já existir

    # Caminho completo onde o arquivo .mp4 será salvo ao final do download
    output_path: str = os.path.join(video_dir, f"{slug}.mp4")

    # ── Verificação: pula silenciosamente se o vídeo já foi baixado ───────────
    # Isso evita re-downloads desnecessários em execuções repetidas do script
    if os.path.exists(output_path):
        print(f"  [PULANDO] Arquivo já existe: {output_path}")
        return

    # ── Opções do yt-dlp ──────────────────────────────────────────────────────
    ydl_opts: dict = {
        # Tenta o melhor MP4; fallback automático para outros formatos disponíveis
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",

        # Define o caminho exato de saída com o nosso slug limpo
        # %(ext)s é substituído automaticamente pela extensão correta (ex: .mp4)
        "outtmpl": os.path.join(video_dir, f"{slug}.%(ext)s"),

        # Modo silencioso: sem barra de progresso, sem logs técnicos
        "quiet": True,

        # Ignora avisos como cookies expirados ou restrições de região
        "no_warnings": True,

        # Continua para o próximo vídeo se este falhar — essencial em loops longos
        "ignoreerrors": True,
    }

    # ── Executa o download ────────────────────────────────────────────────────
    try:
        print(f"  [BAIXANDO] {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])  # Passa a URL como lista (yt-dlp aceita múltiplas)
        print(f"  [OK] Salvo em: {output_path}")
    except Exception as e:
        print(f"  [ERRO] Falha ao baixar '{title}': {e}")


# ─── Orquestrador Principal ───────────────────────────────────────────────────

def download_all() -> None:
    """
    Função principal: lê todos os candidatos do raw_candidates.json e
    baixa cada um deles. Vídeos já baixados são pulados automaticamente.
    """
    # Cria a pasta raiz de destino caso ainda não exista
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Carrega a lista de vídeos candidatos gerada pelo miner.py
    videos: list[dict] = load_candidates()

    if not videos:
        print("[INFO] Nenhum vídeo para baixar.")
        return

    total: int = len(videos)
    print(f"[INFO] {total} vídeo(s) encontrado(s) em '{INPUT_FILE}'. Iniciando downloads...\n")

    # Percorre cada vídeo da lista e tenta baixar
    for i, video in enumerate(videos, start=1):
        # Extrai título e URL com valores padrão seguros caso estejam ausentes
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
