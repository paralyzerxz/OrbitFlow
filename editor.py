# editor.py
# ─────────────────────────────────────────────────────────────────────────────
# RESPONSABILIDADE: Etapa 5 do pipeline — renderização de legendas no vídeo.
#
# Lê o vídeo baixado pelo downloader.py e o arquivo .json gerado pelo
# publisher_helper.py, extrai as legendas da chave "captions" e as sobrepõe
# no vídeo em segmentos de tempo iguais usando MoviePy + ImageMagick local.
#
# FLUXO:
#   main() → load_captions() → create_subtitle_clips() → final_video.mp4
#
# DEPENDÊNCIA: downloader.py e publisher_helper.py devem ter rodado antes
#   para gerar o .mp4 e o .json dentro de ready_to_post/<slug>/.
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip # type: ignore
from moviepy.config import change_settings # type: ignore

# =============================================================================
# CONFIGURAÇÃO DO IMAGEMAGICK
# -----------------------------------------------------------------------------
# O MoviePy precisa do ImageMagick para transformar texto em imagem (TextClip).
# Sem essa configuração, o script não consegue renderizar as legendas.
#
# O ImageMagick está instalado localmente neste projeto (não no sistema),
# dentro da pasta ready_to_post/IMAGEMAGICK/. Apontamos para o magick.exe
# que fica dentro da subpasta da versão instalada.
# =============================================================================
IMAGEMAGICK_BINARY = (
    r"D:\Meus Projetos IDE\OrbitFlow\Shorts"
    r"\ready_to_post\IMAGEMAGICK\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
)
# Informa ao MoviePy onde o ImageMagick está antes de qualquer uso
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})


# Removidas variáveis fixas VIDEO_FOLDER, VIDEO_BASENAME, VIDEO_PATH, JSON_PATH e OUTPUT_PATH
# Agora elas serão injetadas diretamente na função main() ou get() para viabilizar autonomia.


# =============================================================================
# CONFIGURAÇÕES DE ESTILO DAS LEGENDAS
# -----------------------------------------------------------------------------
# Essas constantes controlam a aparência visual do texto sobreposto.
# Altere aqui para personalizar sem precisar mexer na lógica do script.
# =============================================================================
FONT       = "Arial"           # Fonte do texto (deve estar instalada no Windows)
FONT_SIZE  = 70                # Tamanho em pontos — 70 é grande o suficiente para mobile
FONT_COLOR = "yellow"          # Cor do texto: amarelo contrasta bem sobre qualquer fundo
SUBTITLE_POSITION = ("center", "bottom")  # Posição: centralizado na parte inferior da tela


# =============================================================================
# FUNÇÕES
# =============================================================================

def load_captions(json_path: str) -> list[str]:
    """
    Abre o arquivo JSON do vídeo e extrai as frases de legenda.

    O campo "captions" no JSON é uma string única com as frases separadas
    por quebra de linha (\\n). Exemplo do conteúdo:
        "You had no idea\\nThis trick exists\\nNo tools needed"

    Esta função abre o arquivo, lê esse campo e divide em uma lista:
        ["You had no idea", "This trick exists", "No tools needed"]

    Raises:
        FileNotFoundError: se o arquivo JSON não existir.
        KeyError: se a chave "captions" não estiver no JSON.
        ValueError: se "captions" estiver vazio após o parse.
    """
    # Abre o arquivo com codificação UTF-8 (suporta acentos, emojis, etc.)
    with open(json_path, "r", encoding="utf-8") as f:
        data: dict = json.load(f)  # Converte o texto JSON em dicionário Python

    # Lê o campo "captions" — uma string com frases separadas por \n
    raw_captions: str = data["captions"]

    # Divide em linhas, remove espaços extras das bordas e filtra linhas vazias
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
    Cria um TextClip (clip de texto animado) para cada frase de legenda,
    sincronizado com o trecho correspondente do vídeo.

    Lógica de sincronização por segmentos iguais:
      - Divide a duração total do vídeo pelo número de frases
      - Cada frase ocupa exatamente um segmento de tempo

    Exemplo com 8 frases e 40 segundos de vídeo:
      Segmento = 40 / 8 = 5 segundos por frase
      Frase 1 → de 0s a 5s
      Frase 2 → de 5s a 10s
      ... e assim por diante

    Parâmetros:
      phrases        : lista de frases extraídas do JSON
      video_duration : duração total do vídeo em segundos
      video_width    : largura do vídeo em pixels (usada para quebra de linha)
    """
    num_phrases      = len(phrases)
    segment_duration = video_duration / num_phrases  # duração de cada frase em segundos

    subtitle_clips: list[TextClip] = []

    for index, phrase in enumerate(phrases):
        # Calcula o início e o fim deste segmento
        start_time = index * segment_duration
        end_time   = start_time + segment_duration

        # Cria o clip de texto com as configurações de estilo definidas no topo
        # Padrão ADS: Contorno em preto 'stroke_color="black"', 'stroke_width=2' para viabilizar legibilidade universal
        txt_clip = (
            TextClip(
                phrase,
                fontsize=FONT_SIZE,
                font=FONT,
                color=FONT_COLOR,
                stroke_color='black',
                stroke_width=2.5,
                method="caption",           # Modo "caption": quebra de linha automática
                size=(int(video_width * 0.9), None) # Largura: 90% da tela para margem segura
            )
            .set_start(start_time)          # Frase aparece neste instante do vídeo
            .set_end(end_time)              # Frase desaparece neste instante
            .set_position(SUBTITLE_POSITION) # Posição na tela (centro, parte inferior)
        )

        subtitle_clips.append(txt_clip)

        # Mostra o progresso no terminal
        print(
            f"  Legenda [{index + 1:02d}/{num_phrases}] "
            f"{start_time:6.2f}s → {end_time:6.2f}s  |  \"{phrase}\""
        )

    return subtitle_clips


# =============================================================================
# FLUXO PRINCIPAL
# =============================================================================

def main(video_folder: str, video_basename: str) -> str | None:
    """
    Orquestra todo o processo recebendo as variáveis dinamicamente do pipeline.
    Retorna o caminho 'OUTPUT_PATH' se for bem sucedido, senão None.
    """
    video_path = os.path.join(video_folder, f"{video_basename}.mp4")
    json_path = os.path.join(video_folder, f"{video_basename}.json")
    output_path = os.path.join(video_folder, "final_video.mp4")

    print("\n" + "=" * 65)
    print(f"  Editor de Vídeo com Legendas — Animando: {video_basename}")
    print("=" * 65)

    try:
        print(f"\n[1/4] Verificando arquivos...")
        for label, path in [("Vídeo", video_path), ("JSON", json_path)]:
            if not os.path.isfile(path):
                print(f"❌ {label} não encontrado em: {path}")
                return None
            print(f"      ✔ {label}: {path}")

        print(f"\n[2/4] Lendo legendas de: {json_path}")
        phrases = load_captions(json_path)
        print(f"      {len(phrases)} frase(s) encontrada(s).")
        
        # Caso queira testar falha artificialmente: if not phrases: return None

        print(f"\n[3/4] Carregando vídeo: {video_path}")
        video = VideoFileClip(video_path)
        print(f"      Duração : {video.duration:.2f}s")

        print(f"\n      Gerando clip(s) de legenda...")
        subtitle_clips = create_subtitle_clips(phrases, video.duration, video.size[0])

        print(f"\n[4/4] Exportando vídeo final: {output_path}")
        final_video = CompositeVideoClip([video] + subtitle_clips)

        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=video.fps,
            threads=4,
            logger="bar"
        )

        video.close()
        final_video.close()

        print("\n✅ Concluído com sucesso!")
        return output_path
        
    except Exception as e:
        print(f"\n[ERRO EDITOR] Falha ao renderizar: {e}")
        return None

if __name__ == "__main__":
    # Apenas para teste local simulado. Em produção, este script será orquestrado pelo main_pipeline.py.
    print("[Aviso] Executando editor dinâmico via terminal.")
    # Exemplo mockado baseado na estrutura do projeto:
    mock_base = "you_wont_believe_these_5_life_hacks_are_real"
    mock_folder = os.path.join(r"D:\Meus Projetos IDE\OrbitFlow\Shorts\ready_to_post", mock_base)
    main(video_folder=mock_folder, video_basename=mock_base)
