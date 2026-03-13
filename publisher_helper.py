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

INPUT_FILE: str = "transformed_videos.json"
OUTPUT_DIR: str = "ready_to_post"


# ─── Utilitários ──────────────────────────────────────────────────────────────

def load_transformed() -> list[dict]:
    """Lê o arquivo gerado pelo transformer.py."""
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
    Converte um texto em um slug seguro.
    """
    # 1. Normalização básica
    normalized = unicodedata.normalize("NFD", str(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    
    # 2. Limpeza de caracteres
    clean = re.sub(r"[^a-zA-Z0-9\s]", "", ascii_text)
    
    # 3. Formatação do slug
    slug_tmp = re.sub(r"\s+", "_", clean.strip()).lower()
    
    # 4. Truncamento sem usar fatiamento [:] (para evitar o bug do Pylance)
    # Pegamos os primeiros 60 caracteres de forma ultra-segura
    # 4. Truncamento ultra-seguro usando lista (evita bugs de fatiamento e concatenação)
    chars: list[str] = []
    for char in str(slug_tmp):
        if len(chars) < 60:
            chars.append(char)
    
    # Juntamos no final - o linter aceita isso sem erros
    res_final = "".join(chars)
    return str(res_final)

def build_viral_title(hooks: list, original_title: str) -> str:
    """
    Escolhe o melhor gancho (hook) para usar como título do vídeo.
    Usa o primeiro hook disponível; cai de volta ao título original se não houver.
    O título é truncado em 100 chars — limite seguro para YouTube Shorts.
    """
    if hooks and len(str(hooks[0]).strip()) > 0:
        title: str = str(hooks[0]).strip()
    else:
        title = str(original_title).strip()

  # Transformamos em lista, pegamos os 100 primeiros e juntamos. 
    # O VS Code não consegue dar erro de tipagem nessa sequência.
    title_list = list(str(title))
    # 71. Criamos o título curto sem usar fatiamento [:]
    short_title_list: list[str] = []
    for char in title_list:
        if len(short_title_list) < 100:
            short_title_list.append(char)
            
    # 72. Juntamos tudo no final
    res_final = "".join(short_title_list)
    return str(res_final)


def build_pinned_comment(hooks: list, captions: str) -> str:
    """
    Monta um primeiro comentário fixado pensado para engajamento máximo.
    Estrutura:
      - Pergunta de engajamento (call-to-action)
      - Os outros hooks como opções alternativas
      - Incentivo ao follow
    """
    # Linha de abertura — o CTA principal
    lines: list[str] = ["Would you try this? 👇"]

   # Adiciona os hooks restantes pule o primeiro sem usar [1:]
    if len(hooks) > 1:
        lines.append("")
        lines.append("🔥 Other angles we loved:")
        
        # Usamos enumerate para pular o índice 0 de forma segura
        for i, hook in enumerate(hooks):
            if i == 0:
                continue
            lines.append(f" -> {str(hook).strip()}")

    # Primeira linha das legendas dinâmicas como prévia do conteúdo
    if captions:
        first_caption_line: str = str(captions).split("\n")[0].strip()
        if first_caption_line:
            lines.append("")
            lines.append(f'📌 Opening caption: "{first_caption_line}"')

    # CTA final
    lines.append("")
    lines.append("Follow for more viral content every day! 🚀")

    return str("\n".join(lines))


def build_package(video: dict) -> dict:
    """
    Gera o pacote de publicação completo para um único vídeo.
    Retorna um dict com todos os campos necessários para postar.
    """
    hooks: list[str] = [str(h).strip() for h in video.get("hooks", [])]
    original_title: str = str(video.get("title", "Untitled")).strip()
    captions: str = str(video.get("captions", "")).strip()
    url: str = str(video.get("url", "")).strip()
    upload_date: str = str(video.get("upload_date", "")).strip()
    view_count: int = int(video.get("view_count", 0))

    viral_title: str = build_viral_title(hooks, original_title)
    pinned_comment: str = build_pinned_comment(hooks, captions)
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
        "suggested_filename": str(f"{filename_slug}.mp4"),
        "metadata_file": str(f"{filename_slug}.txt"),
    }


def save_package(package: dict, index: int) -> None:
    """
    Salva o pacote de publicação em duas coisas dentro de ready_to_post/:
      1. Um arquivo .txt legível por humanos (para copiar e colar direto no app).
      2. Um arquivo .json com todos os dados estruturados (para automação futura).
    """
    slug: str = slugify(str(package.get("viral_title", f"video_{index}")))
    base_name: str = slug or f"video_{index:03d}"

    txt_path: str = os.path.join(OUTPUT_DIR, f"{base_name}.txt")
    json_path: str = os.path.join(OUTPUT_DIR, f"{base_name}.json")

    # ── Arquivo .txt (colar direto no YouTube/Instagram) ──────────────────────
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

    for i, hook in enumerate(package.get("all_hooks", []), start=1):
        txt_lines.append(f"  {i}. {str(hook)}")

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

    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(txt_lines))
        print(f"  ✓ TXT  → {txt_path}")
    except Exception as e:
        print(f"  ✗ Falha ao salvar TXT: {e}")

    # ── Arquivo .json (para automação futura) ─────────────────────────────────
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
    Lê todos os vídeos transformados, gera os pacotes e salva na pasta ready_to_post/.
    """
    # Cria a pasta de destino se não existir
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    videos: list[dict] = load_transformed()

    if not videos:
        print("[INFO] Nenhum vídeo para processar.")
        return

    print(f"[INFO] Gerando pacotes de publicação para {len(videos)} vídeo(s)...\n")

    for i, video in enumerate(videos, start=1):
        title: str = str(video.get("title", "sem título")).strip()
        print(f"[{i}/{len(videos)}] {title}")

        try:
            package: dict = build_package(video)
            save_package(package, i)
        except Exception as e:
            print(f"  ✗ Falhou: {e}")
            continue

    print(f"\n[OK] Pacotes salvos em '/{OUTPUT_DIR}/'. Pronto para postar! 🚀")
    return


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    publish()
