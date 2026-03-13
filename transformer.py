# transformer.py
# ─────────────────────────────────────────────────────────────────────────────
# RESPONSABILIDADE: Etapa 2 do pipeline — transformação dos vídeos via IA.
#
# Lê os candidatos brutos salvos pelo miner.py (raw_candidates.json), gera uma
# transcrição simulada para cada vídeo e chama o GPT-4o para produzir 3 hooks
# virais em inglês e legendas dinâmicas no estilo TikTok/Reels.
# Os resultados são salvos em transformed_videos.json.
#
# FLUXO:
#   transform() → get_transcript() → transform_with_ai() → save_results()
#              → transformed_videos.json
#
# DEPENDÊNCIA: miner.py deve ter rodado antes para gerar raw_candidates.json.
# PRÓXIMO PASSO: rodar publisher_helper.py para montar os pacotes de publicação.
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
from openai import OpenAI  # type: ignore


# ─── Configuração ─────────────────────────────────────────────────────────────

INPUT_FILE: str = "raw_candidates.json"
OUTPUT_FILE: str = "transformed_videos.json"

client: OpenAI = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))


# ─── Utilitários ──────────────────────────────────────────────────────────────

def load_candidates() -> list[dict]:
    """Lê o arquivo de candidatos brutos gerado pelo miner.py."""
    if not os.path.exists(INPUT_FILE):
        print(f"[ERRO] Arquivo '{INPUT_FILE}' não encontrado. Execute o miner.py primeiro.")
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


def save_results(data: list[dict]) -> None:
    """Salva os vídeos transformados no arquivo de saída."""
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[OK] {len(data)} vídeos salvos em '{OUTPUT_FILE}'.")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar {OUTPUT_FILE}: {e}")


# ─── Transcrição Simulada ──────────────────────────────────────────────────────

def get_transcript(video: dict) -> str:
    """
    Retorna uma transcrição simulada baseada no título do vídeo.
    Em produção, substitua pelo Whisper ou outro serviço de ASR.
    """
    title: str = str(video.get("title", "Untitled video")).strip()
    url: str = str(video.get("url", "")).strip()
    transcript: str = (
        f"This video is titled '{title}'. "
        f"It is available at {url}. "
        "The content shows an impressive demonstration that surprises the audience "
        "and delivers a powerful takeaway in under 60 seconds."
    )
    # Trunca para 1500 chars — evita erros de fatiamento e mantém o prompt enxuto
    return str(transcript)[:1500]  # type: ignore


# ─── Chamada à IA ─────────────────────────────────────────────────────────────

def transform_with_ai(video: dict) -> dict | None:
    """
    Usa o GPT-4o para gerar 3 ganchos virais e legendas dinâmicas em inglês.
    Retorna None se a chamada falhar.
    """
    transcript: str = get_transcript(video)
    title: str = str(video.get("title", "")).strip()

    prompt: str = f"""You are a viral short-video scriptwriter for English-speaking audiences (US, UK, Canada).

VIDEO TITLE: {title}
TRANSCRIPT EXCERPT: {transcript}

Your job:

1. HOOKS (3 options) — Each hook must stop the scroll in the first 2 seconds.
   - Use current slang like: "POV", "Wait for it", "You won't believe", "No way this is real", "This changed everything"
   - Maximum 12 words per hook
   - Do NOT use formal dictionary English

2. DYNAMIC CAPTIONS — Translate and rewrite the transcript as dynamic captions.
   - Maximum 4 words per line
   - Each line on a new line
   - Use punchy, emotional language
   - Match the energy of viral TikTok/Reels content

Respond ONLY in this exact JSON format (no markdown, no explanation):
{{
  "hooks": ["hook 1", "hook 2", "hook 3"],
  "captions": "line1\\nline2\\nline3\\n..."
}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=800,
    )

    raw_content: str = str(response.choices[0].message.content or "").strip()

    # Remove blocos de markdown caso a IA os inclua mesmo sendo instruída a não
    raw_content = raw_content.replace("```json", "").replace("```", "").strip()

    parsed: dict = json.loads(raw_content)

    hooks: list[str] = [str(h).strip() for h in parsed.get("hooks", [])]
    captions: str = str(parsed.get("captions", "")).strip()

    return {
        "id": str(video.get("id", "")).strip(),
        "title": str(video.get("title", "")).strip(),
        "url": str(video.get("url", "")).strip(),
        "view_count": int(video.get("view_count", 0)),
        "upload_date": str(video.get("upload_date", "")).strip(),
        "hooks": hooks,
        "captions": captions,
    }


# ─── Orquestrador Principal ───────────────────────────────────────────────────

def transform() -> None:
    """
    Lê todos os candidatos, processa cada um com a IA e salva os resultados.
    Vídeos que falharem são ignorados sem interromper o processo.
    """
    candidates: list[dict] = load_candidates()

    if not candidates:
        print("[INFO] Nenhum candidato para processar.")
        return

    print(f"[INFO] Processando {len(candidates)} vídeos com GPT-4o...\n")

    processed_list: list[dict] = []

    for i, video in enumerate(candidates, start=1):
        title: str = str(video.get("title", "sem título")).strip()
        print(f"[{i}/{len(candidates)}] Transformando: {title}")

        try:
            result = transform_with_ai(video)
            if result:
                processed_list.append(result)
                print(f"  ✓ Hook 1: {result['hooks'][0] if result['hooks'] else 'N/A'}")
        except Exception as e:
            print(f"  ✗ Falhou: {e}")
            continue

    if processed_list:
        print(f"\n[RESULTADO] {len(processed_list)} vídeos transformados com sucesso.")
        save_results(processed_list)
    else:
        print("\n[RESULTADO] Nenhum vídeo foi transformado com sucesso.")


if __name__ == "__main__":
    transform()
