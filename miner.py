# miner.py
# ─────────────────────────────────────────────────────────────────────────────
# RESPONSABILIDADE: Etapa 1 do pipeline — coleta de vídeos candidatos.
#
# Busca vídeos no YouTube usando yt-dlp com base em termos de busca pré-definidos,
# filtra por número mínimo de visualizações e data de upload (últimos 7 dias),
# e salva os resultados em raw_candidates.json, removendo duplicatas automaticamente.
#
# FLUXO:
#   mine() → fetch_videos() → save_to_json() → raw_candidates.json
#
# PRÓXIMO PASSO: rodar transformer.py para processar o arquivo gerado.
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
from datetime import datetime, timedelta
import yt_dlp  # type: ignore


# ─── Configuração ─────────────────────────────────────────────────────────────

OUTPUT_FILE: str = "raw_candidates.json"

SEARCH_TERMS: list[str] = [
    "viral life hacks",
    "amazing facts",
    "satisfying videos",
    "mind blowing facts",
    "life changing tips",
]

MAX_RESULTS_PER_TERM: int = 15
MIN_VIEWS: int = 50_000


# ─── Utilitários ──────────────────────────────────────────────────────────────

def get_cutoff_date() -> str:
    """Retorna a data de 7 dias atrás no formato YYYYMMDD."""
    cutoff = datetime.now() - timedelta(days=7)
    return cutoff.strftime("%Y%m%d")


def load_existing_candidates() -> list[dict]:
    """Lê o arquivo de candidatos existentes. Retorna lista vazia se não existir."""
    if not os.path.exists(OUTPUT_FILE):
        return []
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Garante que o retorno é sempre list[dict]
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
            return []
    except Exception as e:
        print(f"[AVISO] Falha ao ler {OUTPUT_FILE}: {e}")
        return []


def save_to_json(data: list[dict]) -> None:
    """
    Lê o arquivo atual, mescla com os novos dados,
    remove duplicados pela URL e salva tudo de volta.
    """
    # Carrega o que já estava salvo
    existing: list[dict] = load_existing_candidates()

    # Cria um set com as URLs já existentes para comparação O(1)
    existing_urls: set[str] = {str(item.get("url", "")) for item in existing}

    # Filtra apenas os novos vídeos que ainda não estão salvos
    new_items: list[dict] = [
        item for item in data if str(item.get("url", "")) not in existing_urls
    ]

    if not new_items:
        print("[INFO] Nenhum vídeo novo para salvar.")
        return

    # Mescla e salva
    merged: list[dict] = existing + new_items
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=4)
        print(f"[OK] Salvos {len(new_items)} novos vídeos. Total no arquivo: {len(merged)}")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar candidatos: {e}")


# ─── Busca de Vídeos ──────────────────────────────────────────────────────────

def fetch_videos(search_query: str, max_results: int, min_views: int) -> list[dict]:
    """
    Busca vídeos no YouTube via yt-dlp e retorna apenas os que passam nos filtros
    de visualizações e data de upload (últimos 7 dias).
    """
    results: list[dict] = []
    cutoff_date: str = get_cutoff_date()

    ydl_opts: dict = {
        "extract_flat": False,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_url: str = f"ytsearch{max_results}:{search_query}"
            print(f"[BUSCANDO] '{search_query}'...")

            info = ydl.extract_info(search_url, download=False)

            if not info or "entries" not in info:
                return results

            entries = info["entries"]
            if not isinstance(entries, list):
                return results

            for entry in entries:
                if not entry or not isinstance(entry, dict):
                    continue

                try:
                    # Casting explícito para str antes de qualquer operação de string
                    video_id: str = str(entry.get("id", ""))
                    title: str = str(entry.get("title", ""))
                    url: str = str(entry.get("webpage_url", f"https://www.youtube.com/watch?v={video_id}"))

                    # view_count pode ser None — usa 0 como fallback seguro
                    view_count_raw = entry.get("view_count")
                    view_count: int = int(view_count_raw) if isinstance(view_count_raw, (int, float)) else 0

                    # str() explícito garante ao Pylance que é uma str pura antes do fatiamento
                    upload_date_raw: str = str(entry.get("upload_date", "")).strip()
                    upload_date: str = "".join(list(upload_date_raw)[:8]) if len(upload_date_raw) >= 8 else ""  # type: ignore

                    # ── Filtros ──
                    if view_count < min_views:
                        continue

                    if not upload_date or upload_date < cutoff_date:
                        continue

                    results.append({
                        "id": video_id,
                        "title": title,
                        "url": url,
                        "view_count": view_count,
                        "upload_date": upload_date,
                    })

                except Exception as e:
                    print(f"[AVISO] Erro ao processar entrada: {e}")
                    continue

    except Exception as e:
        print(f"[ERRO] Falha na busca yt-dlp: {e}")

    return results


# ─── Orquestrador Principal ───────────────────────────────────────────────────

def mine() -> None:
    """
    Itera pelos termos de busca, coleta vídeos novos e salva no arquivo JSON,
    sem duplicar entradas já existentes.
    """
    all_new_videos: list[dict] = []

    # Set de URLs coletadas nessa mesma execução para evitar duplicados internos
    seen_urls_this_run: set[str] = set()

    for term in SEARCH_TERMS:
        fetched: list[dict] = fetch_videos(
            search_query=term,
            max_results=MAX_RESULTS_PER_TERM,
            min_views=MIN_VIEWS,
        )

        for video in fetched:
            url: str = str(video.get("url", ""))
            if url and url not in seen_urls_this_run:
                all_new_videos.append(video)
                seen_urls_this_run.add(url)

    if all_new_videos:
        print(f"\n[RESULTADO] {len(all_new_videos)} vídeos candidatos encontrados nesta execução.")
        save_to_json(all_new_videos)
    else:
        print("\n[RESULTADO] Nenhum vídeo novo passou nos filtros desta execução.")


if __name__ == "__main__":
    mine()
