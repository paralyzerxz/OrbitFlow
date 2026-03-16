import os
import json
import google.generativeai as genai # type: ignore

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = r"D:\Meus Projetos IDE\Orbit Flow Global\Shorts"
INPUT_FILE = os.path.join(BASE_DIR, "raw_candidates.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "transformed_videos.json")

genai.configure(api_key="AIzaSyDiC-MhrQspEywrXp10kwEmMT8Qzy9nldE")
model = genai.GenerativeModel('models/gemini-1.5-flash')

# ─────────────────────────────────────────────────────────────────────────────
# UTILITÁRIOS
# ─────────────────────────────────────────────────────────────────────────────
def load_candidates() -> list[dict]:
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
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[OK] {len(data)} vídeos salvos em '{OUTPUT_FILE}'.")
        print("Arquivo transformed_videos.json criado com sucesso!")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar {OUTPUT_FILE}: {e}")

def get_transcript(video: dict) -> str:
    title: str = str(video.get("title", "Untitled video")).strip()
    url: str = str(video.get("url", "")).strip()
    transcript: str = (
        f"This video is titled '{title}'. "
        f"It is available at {url}. "
        "The content shows an impressive demonstration that surprises the audience "
        "and delivers a powerful takeaway in under 60 seconds."
    )
    # Limita a 1500 caracteres para não estourar o limite de tokens
    safe_transcript: str = str(transcript)
    
    chars: list[str] = []
    for char in safe_transcript:
        if len(chars) < 1500:
            chars.append(char)
            
    return str("".join(chars))

# ─────────────────────────────────────────────────────────────────────────────
# IA
# ─────────────────────────────────────────────────────────────────────────────
def transform_with_ai(video: dict) -> dict | None:
    title: str = str(video.get("title", "")).strip()
    transcript: str = get_transcript(video)

    prompt: str = f"""You are a top-tier viral short-video scriptwriter for a Global English-speaking audience.
Your content must resonate universally across the US, UK, Canada, Australia, and New Zealand.

VIDEO TITLE: {title}
TRANSCRIPT EXCERPT: {transcript}

Your job:
1. VIRAL TITLE: Generate a clickbait, highly engaging viral title for this video.
2. HOOKS (3 options) — Each hook must stop the scroll in the first 2 seconds.
   - Use clear, universally understood modern language. Avoid hyper-local slang.
   - Max 12 words per hook. Keep the energy high and emotional.
3. DYNAMIC CAPTIONS — Translate and rewrite the transcript as dynamic captions.
   - MAXIMUM 4 WORDS PER LINE.
   - Each line on a new line.

Respond ONLY in this exact JSON format (no markdown, no explanation, no code blocks):
{{
  "viral_title": "The Viral Title Here",
  "hooks": ["hook 1", "hook 2", "hook 3"],
  "captions": "line1\\nline2\\nline3\\n..."
}}"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        raw_content: str = response.text.strip()
        print(f"\n[DEBUG IA] Resposta bruta da IA:\n{raw_content}\n")
    except Exception as e:
        print(f"\n[ERRO IA] Falha de comunicação com a IA API. Detalhes: {e}\n")
        return None

    # Segurança caso retorne markdown formating blocks por acidente
    raw_content = raw_content.replace("```json", "").replace("```", "").strip()

    try:
        parsed: dict = json.loads(raw_content)
    except Exception as e:
        print(f"\n[ERRO JSON] Resposta inválida da IA:\n{raw_content}\n")
        return None

    return {
        "id": str(video.get("id", "")).strip(),
        "title": str(parsed.get("viral_title", title)).strip(),
        "original_title": title,
        "url": str(video.get("url", "")).strip(),
        "view_count": int(video.get("view_count", 0)),
        "upload_date": str(video.get("upload_date", "")).strip(),
        "hooks": [str(h).strip() for h in parsed.get("hooks", [])],
        "captions": str(parsed.get("captions", "")).strip(),
    }

# ─────────────────────────────────────────────────────────────────────────────
# EXECUÇÃO DA ETAPA
# ─────────────────────────────────────────────────────────────────────────────
def transform() -> None:
    candidates: list[dict] = load_candidates()
    if not candidates:
        print("[INFO] Nenhum candidato para processar.")
        return

    print(f"[INFO] Processando {len(candidates)} vídeos com Gemini 1.5 Flash...\n")
    processed_list: list[dict] = []

    for i, video in enumerate(candidates, start=1):
        title: str = str(video.get("title", "sem título")).strip()
        print(f"[{i}/{len(candidates)}] Transformando: {title}")

        result = transform_with_ai(video)
        if result:
            processed_list.append(result)
            print(f"  OK Processado com Sucesso!")
        else:
            print(f"  X Falha na IA. Pulando.")

    if processed_list:
        print(f"\n[RESULTADO] {len(processed_list)} vídeos concluídos.")
        save_results(processed_list)
    else:
        print("\n[RESULTADO] Nenhum arquivo gerado na transformação.")

if __name__ == "__main__":
    transform()
