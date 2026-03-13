# setup_test.py
# ─────────────────────────────────────────────────────────────────────────────
# OBJETIVO: Criar um arquivo transformed_videos.json com dados fictícios
#           para testar o publisher_helper.py sem precisar da OpenAI.
#
# BIBLIOTECA: Só usamos 'json', que já vem instalada com o Python.
#             Não é necessário instalar nada (sem pip install).
# ─────────────────────────────────────────────────────────────────────────────

import json


# ─── Dados Fictícios ──────────────────────────────────────────────────────────

# Aqui definimos um vídeo de exemplo no formato que o publisher_helper.py espera.
# Pense nisso como um "mock" — um dado falso que imita o dado verdadeiro.
# Cada chave (ex: "title") corresponde exatamente ao que o transformer.py produziria.

fake_video: dict = {

    # ID único do vídeo (normalmente vem do YouTube via yt-dlp)
    "id": "dQw4w9WgXcQ",

    # Título original do vídeo (pode estar em outro idioma)
    "title": "5 Truques de Casa Que Vão Mudar Sua Vida",

    # URL do vídeo fonte
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",

    # Número de visualizações no momento da coleta
    "view_count": 4820000,

    # Data de upload no formato YYYYMMDD (padrão do yt-dlp)
    "upload_date": "20260310",

    # Título viral em inglês gerado pela IA (aqui escrevemos manualmente para o teste)
    "viral_title": "You Won't Believe These 5 Life Hacks Are Real",

    # Lista de 3 ganchos (hooks) virais — frases de impacto para parar o scroll
    "hooks": [
        "You Won't Believe These 5 Life Hacks Are Real",
        "POV: You Finally Figured Out How to Hack Your House",
        "Wait For It... This Changed Everything At Home"
    ],

    # Comentário fixado já formatado — para copiar e colar no YouTube/Instagram
    "fixed_comment": (
        "Would you try this? 👇\n"
        "\n"
        "🔥 Other angles we loved:\n"
        "  → POV: You Finally Figured Out How to Hack Your House\n"
        "  → Wait For It... This Changed Everything At Home\n"
        "\n"
        "Follow for more viral content every day! 🚀"
    ),

    # Legendas dinâmicas — uma frase curta por linha (máximo 4 palavras cada)
    "captions": (
        "You had no idea\n"
        "This trick exists\n"
        "No tools needed\n"
        "Just 30 seconds\n"
        "Your life changes\n"
        "Try it now\n"
        "Share with someone\n"
        "Who needs this"
    ),
}


# ─── Montagem da Lista ────────────────────────────────────────────────────────

# O transformed_videos.json é uma lista de vídeos.
# Mesmo que seja só um, ele precisa estar dentro de uma lista [].
# Isso é importante porque o publisher_helper.py usa: for video in videos
transformed_videos: list[dict] = [fake_video]


# ─── Escrita no Arquivo ───────────────────────────────────────────────────────

# Nome do arquivo de saída — deve ser exatamente este para o publisher_helper.py encontrar.
OUTPUT_FILE: str = "transformed_videos.json"

# Abrimos o arquivo em modo de escrita ("w") com suporte a emojis (utf-8).
# Se o arquivo já existir, ele será sobrescrito — útil para resetar os testes.
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    # json.dump transforma o dict Python em texto JSON dentro do arquivo.
    # ensure_ascii=False → preserva emojis e acentos sem converter para \uXXXX
    # indent=4          → indenta o JSON para facilitar a leitura
    json.dump(transformed_videos, f, ensure_ascii=False, indent=4)


# ─── Confirmação no Console ───────────────────────────────────────────────────

# Mensagem final para confirmação visual no terminal.
print("✅ [TESTE] Arquivo 'transformed_videos.json' criado! Agora você já pode rodar o 'python publisher_helper.py'")
