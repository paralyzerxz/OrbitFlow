# editor.py
# Script responsável por sobrepor legendas automáticas em um vídeo MP4
# usando MoviePy v1.0.3. As legendas são lidas do arquivo .json do vídeo,
# dividindo o clipe em segmentos iguais — um por frase da chave "captions".

import os
import json
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings

# =============================================================================
# CONFIGURAÇÃO DO IMAGEMAGICK
# -----------------------------------------------------------------------------
# O MoviePy usa o ImageMagick para renderizar texto como imagem (TextClip).
# Precisamos apontar explicitamente para o executável "magick.exe".
#
# Estrutura instalada localmente:
#   ready_to_post\
#     IMAGEMAGICK\
#       ImageMagick-7.1.2-Q16-HDRI\
#         magick.exe   ← executável real do ImageMagick
# =============================================================================
IMAGEMAGICK_BINARY = (
    r"D:\Meus Projetos IDE\Antigravity\Shorts"
    r"\ready_to_post\IMAGEMAGICK\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
)
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})


# =============================================================================
# CAMINHOS DOS ARQUIVOS
# -----------------------------------------------------------------------------
# LÓGICA DE DIRETÓRIOS (padrão ADS):
#
#   Raiz do projeto:
#     D:\Meus Projetos IDE\Antigravity\Shorts\
#
#   Subpasta de trabalho (ready_to_post):
#     └── ready_to_post\
#         └── you_wont_believe_these_5_life_hacks_are_real\  ← pasta do vídeo
#               ├── you_wont_believe_these_5_life_hacks_are_real.mp4  ← entrada
#               ├── you_wont_believe_these_5_life_hacks_are_real.json ← dados
#               └── final_video.mp4                                   ← saída
#
# Usamos caminhos ABSOLUTOS (raw strings r"...") para evitar qualquer
# ambiguidade em relação ao CWD (Current Working Directory) do terminal.
# Com caminhos absolutos, o script funciona independentemente de onde
# você o execute (ex: python editor.py ou python Shorts/editor.py).
# =============================================================================

# Pasta-mãe que contém o vídeo e o JSON — único lugar a editar para mudar o vídeo
VIDEO_FOLDER = (
    r"D:\Meus Projetos IDE\Antigravity\Shorts"
    r"\ready_to_post\you_wont_believe_these_5_life_hacks_are_real"
)

# Nome-base compartilhado entre o .mp4 e o .json (convenção do pipeline)
VIDEO_BASENAME = "you_wont_believe_these_5_life_hacks_are_real"

# Caminho completo do vídeo de entrada
VIDEO_PATH = os.path.join(VIDEO_FOLDER, f"{VIDEO_BASENAME}.mp4")

# Caminho completo do arquivo JSON com os metadados (inclui chave "captions")
JSON_PATH = os.path.join(VIDEO_FOLDER, f"{VIDEO_BASENAME}.json")

# Caminho completo do vídeo final gerado pelo script
OUTPUT_PATH = os.path.join(VIDEO_FOLDER, "final_video.mp4")


# =============================================================================
# CONFIGURAÇÕES DE ESTILO DAS LEGENDAS
# -----------------------------------------------------------------------------
# Essas constantes controlam a aparência visual do texto sobreposto.
# Altere-as para personalizar fontes, tamanhos e cores sem mexer na lógica.
# =============================================================================
FONT       = "Arial"           # Fonte (deve estar instalada no sistema)
FONT_SIZE  = 70                # Tamanho em pontos
FONT_COLOR = "yellow"          # Cor do texto (nome CSS ou hex, ex: "#FFD700")
SUBTITLE_POSITION = ("center", "bottom")  # Alinhamento: centralizado, parte inferior


# =============================================================================
# FUNÇÕES
# =============================================================================

def load_captions(json_path: str) -> list[str]:
    """
    Lê o arquivo JSON do vídeo e extrai as frases da chave "captions".

    Estrutura esperada do JSON:
        {
            "captions": "Frase 1\\nFrase 2\\nFrase 3",
            ...outros campos...
        }

    O campo "captions" é uma string com frases separadas por '\\n'.
    Esta função divide essa string numa lista de frases limpas.

    Raises:
        FileNotFoundError: se o arquivo JSON não existir no caminho informado.
        KeyError: se a chave "captions" não estiver no JSON.
        ValueError: se "captions" estiver vazio após o parse.
    """
    # Abre e decodifica o JSON (UTF-8 para suportar acentos e emojis)
    with open(json_path, "r", encoding="utf-8") as f:
        data: dict = json.load(f)

    # Extrai o campo "captions" (string com \n entre frases)
    raw_captions: str = data["captions"]

    # Divide em linhas, remove espaços extras e filtra linhas vazias
    phrases: list[str] = [line.strip() for line in raw_captions.splitlines() if line.strip()]

    if not phrases:
        raise ValueError(f'A chave "captions" está vazia em: {json_path}')

    return phrases


def create_subtitle_clips(
    phrases: list[str],
    video_duration: float,
    video_width: int
) -> list[TextClip]:
    """
    Gera uma lista de TextClips sincronizados ao vídeo.

    Lógica de sincronização:
        - O vídeo é dividido em N segmentos de duração igual.
        - Cada segmento recebe uma frase (index = segmento).
        - Exemplo com 8 frases e 40s de vídeo → segmentos de 5s cada.

    Parâmetros:
        phrases        : lista de frases extraídas do JSON
        video_duration : duração total do vídeo em segundos
        video_width    : largura do vídeo em pixels (para quebra de linha)
    """
    num_phrases     = len(phrases)
    segment_duration = video_duration / num_phrases  # segundos por frase

    subtitle_clips: list[TextClip] = []

    for index, phrase in enumerate(phrases):
        start_time = index * segment_duration          # início do segmento
        end_time   = start_time + segment_duration     # fim do segmento

        txt_clip = (
            TextClip(
                phrase,
                fontsize=FONT_SIZE,
                font=FONT,
                color=FONT_COLOR,
                method="caption",           # habilita quebra de linha automática
                size=(video_width, None)    # largura do vídeo; altura dinâmica
            )
            .set_start(start_time)
            .set_end(end_time)
            .set_position(SUBTITLE_POSITION)
        )

        subtitle_clips.append(txt_clip)
        print(
            f"  Legenda [{index + 1:02d}/{num_phrases}] "
            f"{start_time:6.2f}s → {end_time:6.2f}s  |  \"{phrase}\""
        )

    return subtitle_clips


# =============================================================================
# FLUXO PRINCIPAL
# =============================================================================

def main() -> None:
    """Orquestra a leitura, geração de legendas e exportação do vídeo final."""

    print("=" * 65)
    print("  Editor de Vídeo com Legendas — MoviePy v1.0.3")
    print("=" * 65)

    # ------------------------------------------------------------------
    # ETAPA 1 — Verificar se os arquivos existem antes de abrir
    # ------------------------------------------------------------------
    # Fazemos as verificações upfront para dar mensagens de erro claras.
    print(f"\n[1/4] Verificando arquivos...")

    for label, path in [("Vídeo", VIDEO_PATH), ("JSON", JSON_PATH)]:
        if not os.path.isfile(path):
            raise FileNotFoundError(
                f"\n❌ {label} não encontrado!\n"
                f"   Caminho verificado: {path}\n"
                f"   Confira se VIDEO_FOLDER e VIDEO_BASENAME estão corretos."
            )
        print(f"      ✔ {label}: {path}")

    # ------------------------------------------------------------------
    # ETAPA 2 — Carregar frases do JSON
    # ------------------------------------------------------------------
    print(f"\n[2/4] Lendo legendas de: {JSON_PATH}")
    phrases = load_captions(JSON_PATH)
    print(f"      {len(phrases)} frase(s) encontrada(s):")
    for i, p in enumerate(phrases, 1):
        print(f"        {i}. {p}")

    # ------------------------------------------------------------------
    # ETAPA 3 — Carregar vídeo e gerar clips de legenda
    # ------------------------------------------------------------------
    print(f"\n[3/4] Carregando vídeo: {VIDEO_PATH}")
    video = VideoFileClip(VIDEO_PATH)
    print(f"      Duração : {video.duration:.2f}s")
    print(f"      Resolução: {video.size[0]}x{video.size[1]}px")
    print(f"      FPS      : {video.fps}")

    print(f"\n      Gerando {len(phrases)} clip(s) de legenda...")
    subtitle_clips = create_subtitle_clips(phrases, video.duration, video.size[0])

    # ------------------------------------------------------------------
    # ETAPA 4 — Combinar e exportar
    # ------------------------------------------------------------------
    print(f"\n[4/4] Exportando vídeo final: {OUTPUT_PATH}")
    final_video = CompositeVideoClip([video] + subtitle_clips)

    final_video.write_videofile(
        OUTPUT_PATH,
        codec="libx264",    # codec H.264 — máxima compatibilidade
        audio_codec="aac",  # áudio AAC — padrão para MP4
        fps=video.fps,      # preserva FPS original do vídeo
        threads=4,          # usa 4 threads para renderização paralela
        logger="bar"        # exibe barra de progresso no terminal
    )

    # Libera handles de arquivo e memória
    video.close()
    final_video.close()

    print("\n✅ Concluído com sucesso!")
    print(f"   Arquivo salvo em:\n   {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
