# publisher_helper.py
# ─────────────────────────────────────────────────────────────────────────────
# RESPONSABILIDADE: Etapa 3 do pipeline — geração dos pacotes de publicação.
#
# Lê os vídeos já transformados pela IA (transformed_videos.json) e gera,
# para cada um, um pacote completo pronto para postar: título viral, hooks,
# comentário fixado e legendas dinâmicas — salvos em .txt e .json dentro
# da pasta ready_to_post/.
#
# FLUXO:
#   publish() → build_package() → save_package() → ready_to_post/<slug>.txt/.json
#
# DEPENDÊNCIA: transformer.py deve ter rodado antes para gerar transformed_videos.json.
# TESTE SEM IA : rode setup_test.py para criar um transformed_videos.json fictício.
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
import re
import unicodedata


# ─── Configuração ─────────────────────────────────────────────────────────────

# Arquivo de entrada: vídeos transformados pelo transformer.py
INPUT_FILE: str = "transformed_videos.json"

# Pasta onde os pacotes prontos para publicação serão salvos
OUTPUT_DIR: str = "ready_to_post"


# ─── Utilitários ──────────────────────────────────────────────────────────────

def load_transformed() -> list[dict]:
    """
    Lê o arquivo transformed_videos.json gerado pelo transformer.py.
    Retorna lista vazia se o arquivo não existir, sem travar o programa.
    """
    if not os.path.exists(INPUT_FILE):
        print(f"[ERRO] Arquivo '{INPUT_FILE}' não encontrado. Execute o transformer.py primeiro.")
        return []
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
            return []
    except Exception as e:
        print(f"[ERRO] Falha ao ler {INPUT_FILE}: {e}")
        return []


def slugify(text: str) -> str:
    """
    Converte qualquer texto em um 'slug' — um nome seguro para usar como
    nome de arquivo ou pasta, sem espaços nem caracteres especiais.

    Exemplo: "You Won't Believe This!" → "you_wont_believe_this"

    Passos:
      1. Remove acentos (á → a, ç → c, etc.)
      2. Remove tudo que não seja letra, número ou espaço
      3. Troca espaços por underscores e coloca em minúsculo
      4. Limita a 60 caracteres para nomes de arquivo razoáveis
    """
    # Passo 1: normaliza e remove acentos Unicode
    normalized = unicodedata.normalize("NFD", str(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")

    # Passo 2: remove tudo que não for letra, número ou espaço
    clean = re.sub(r"[^a-zA-Z0-9\s]", "", ascii_text)

    # Passo 3: converte espaços em underscores e deixa tudo minúsculo
    slug_tmp = re.sub(r"\s+", "_", clean.strip()).lower()

    # Passo 4: trunca em 60 caracteres de forma segura (sem slicing [:])
    chars: list[str] = []
    for char in str(slug_tmp):
        if len(chars) < 60:
            chars.append(char)

    return str("".join(chars))


def build_viral_title(title: str, original_title: str) -> str:
    """
    Escolhe o melhor título para o vídeo a ser postado.

    O transformer.py com Gemini já nos entrega um 'viral_title' no campo "title".
    Usamos ele, ou caímos pro original se falhar.

    O título é truncado em 100 caracteres — limite seguro para YouTube Shorts.
    """
    # Usa o título retornado pelo Gemini
    if title and len(str(title).strip()) > 0:
        final_title: str = str(title).strip()
    else:
        # Fallback: usa o título original do vídeo
        final_title = str(original_title).strip()

    # Trunca sem usar fatiamento [:] para evitar erros de tipagem
    short_title_list: list[str] = []
    for char in list(str(final_title)):
        if len(short_title_list) < 100:
            short_title_list.append(char)

    return str("".join(short_title_list))


def build_pinned_comment(hooks: list, captions: str) -> str:
    """
    Monta o primeiro comentário fixado — aquele que o criador posta logo após
    publicar o vídeo para incentivar engajamento (likes, follows, respostas).

    Estrutura do comentário:
      - Pergunta para o espectador responder (call-to-action)
      - Os outros hooks como opções alternativas para curiosidade
      - Prévia da primeira legenda do vídeo
      - Convite para seguir o canal
    """
    # Linha de abertura: pergunta que incentiva o espectador a interagir
    lines: list[str] = ["Would you try this? 👇"]

    # Adiciona os hooks alternativos (pula o primeiro, que virou o título)
    if len(hooks) > 1:
        lines.append("")
        lines.append("🔥 Other angles we loved:")

        # Percorre a lista e pula o índice 0 com enumerate (sem usar [1:])
        for i, hook in enumerate(hooks):
            if i == 0:
                continue  # Pula o primeiro hook (já usado como título)
            lines.append(f" -> {str(hook).strip()}")

    # Adiciona a primeira linha das legendas como prévia do conteúdo
    if captions:
        first_caption_line: str = str(captions).split("\n")[0].strip()
        if first_caption_line:
            lines.append("")
            lines.append(f'📌 Opening caption: "{first_caption_line}"')

    # CTA final: convite para seguir o canal
    lines.append("")
    lines.append("Follow for more viral content every day! 🚀")

    # Une todas as linhas com quebra de linha
    return str("\n".join(lines))


def build_package(video: dict) -> dict:
    """
    Recebe um vídeo transformado e monta o pacote completo de publicação.

    O pacote contém tudo o que o criador precisa para postar:
      - Título viral pronto para colar no YouTube/Instagram
      - Todos os hooks gerados (para testes A/B)
      - Comentário fixado pronto para copiar
      - Legendas dinâmicas para sobrepor no vídeo
      - Nome sugerido para o arquivo .mp4
    """
    # Extrai e limpa os campos do vídeo
    hooks: list[str] = [str(h).strip() for h in video.get("hooks", [])]
    # O transformer salva o texto gerado por IA no campo "title"
    # e o título do YouTube no campo "original_title".
    title_from_ia: str = str(video.get("title", "")).strip()
    original_title: str = str(video.get("original_title", "Untitled")).strip()
    captions: str = str(video.get("captions", "")).strip()
    url: str = str(video.get("url", "")).strip()
    upload_date: str = str(video.get("upload_date", "")).strip()
    view_count: int = int(video.get("view_count", 0))

    # Gera o título viral e o comentário fixado
    viral_title: str = build_viral_title(title_from_ia, original_title)
    pinned_comment: str = build_pinned_comment(hooks, captions)

    # Gera o slug do nome de arquivo a partir do título viral
    # Fallback para o título original caso o viral esteja vazio
    filename_slug: str = slugify(viral_title) or slugify(original_title) or "untitled"

    return {
        "source_url": url,
        "original_title": original_title,
        "upload_date": upload_date,
        "view_count": view_count,
        "viral_title": viral_title,
        "all_hooks": hooks,
        "pinned_comment": pinned_comment,
        "captions": captions,
        "suggested_filename": str(f"{filename_slug}.mp4"),  # Nome do .mp4 a baixar
        "metadata_file": str(f"{filename_slug}.txt"),       # Nome do .txt de publicação
    }


def save_package(package: dict, index: int) -> None:
    """
    Salva o pacote de publicação em dois formatos dentro de ready_to_post/:

      1. Arquivo .txt — legível e formatado para copiar e colar direto no app
         (título, hooks, comentário fixado, legendas)

      2. Arquivo .json — estruturado para uso futuro por scripts de automação
         (downloader.py, editor.py, etc.)

    Ambos os arquivos usam o mesmo slug como nome base.
    """
    # Gera o nome base do arquivo a partir do título viral
    slug: str = slugify(str(package.get("viral_title", f"video_{index}")))
    base_name: str = slug or f"video_{index:03d}"

    # Caminhos completos dos arquivos de saída (pasta do pacote específico)
    folder_path: str = os.path.join(OUTPUT_DIR, base_name)
    os.makedirs(folder_path, exist_ok=True)
    
    txt_path: str = os.path.join(folder_path, f"{base_name}.txt")
    json_path: str = os.path.join(folder_path, f"{base_name}.json")

    # ── Arquivo .txt: formatado para copiar e colar no app de publicação ──────
    txt_lines: list[str] = [
        "─" * 60,
        f"📹 SUGGESTED FILENAME : {package.get('suggested_filename', '')}",
        f"🔗 SOURCE URL         : {package.get('source_url', '')}",
        f"📅 UPLOAD DATE        : {package.get('upload_date', '')}",
        f"👁️  VIEWS (original)   : {package.get('view_count', 0):,}",
        "─" * 60,
        "",
        "🏷️  VIRAL TITLE (paste into YouTube/Instagram title field):",
        str(package.get("viral_title", "")),
        "",
        "🎯 ALL HOOKS (choose one or A/B test them):",
    ]

    # Adiciona cada hook numerado
    for i, hook in enumerate(package.get("all_hooks", []), start=1):
        txt_lines.append(f"  {i}. {str(hook)}")

    # Continua com o comentário fixado e as legendas
    txt_lines += [
        "",
        "📌 PINNED COMMENT (copy and pin this right after posting):",
        "─" * 40,
        str(package.get("pinned_comment", "")),
        "─" * 40,
        "",
        "🎬 DYNAMIC CAPTIONS:",
        str(package.get("captions", "")),
        "",
        "─" * 60,
    ]

    # Salva o arquivo .txt
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(txt_lines))
        print(f"  ✓ TXT  → {txt_path}")
    except Exception as e:
        print(f"  ✗ Falha ao salvar TXT: {e}")

    # ── Arquivo .json: para uso por outros scripts do pipeline ────────────────
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(package, f, ensure_ascii=False, indent=4)
        print(f"  ✓ JSON → {json_path}")
    except Exception as e:
        print(f"  ✗ Falha ao salvar JSON: {e}")

    return


# ─── Orquestrador Principal ───────────────────────────────────────────────────

def publish() -> None:
    """
    Função principal: lê todos os vídeos transformados e gera um pacote
    de publicação completo para cada um deles na pasta ready_to_post/.
    """
    # Garante que a pasta de destino existe antes de tentar escrever nela
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Carrega os vídeos transformados pelo transformer.py
    videos: list[dict] = load_transformed()

    if not videos:
        print("[INFO] Nenhum vídeo para processar.")
        return

    print(f"[INFO] Gerando pacotes de publicação para {len(videos)} vídeo(s)...\n")

    for i, video in enumerate(videos, start=1):
        title: str = str(video.get("title", "sem título")).strip()
        print(f"[{i}/{len(videos)}] {title}")

        try:
            # Monta o dicionário completo com todos os dados para publicação
            package: dict = build_package(video)
            # Salva os arquivos .txt e .json na pasta ready_to_post/
            save_package(package, i)
        except Exception as e:
            print(f"  ✗ Falhou: {e}")
            continue

    print(f"\n[OK] Pacotes salvos em '/{OUTPUT_DIR}/'. Pronto para postar! 🚀")
    return


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    publish()
