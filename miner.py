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

# Nome do arquivo onde os vídeos encontrados serão salvos
OUTPUT_FILE: str = "raw_candidates.json"

# Palavras-chave de busca — o script pesquisa cada uma dessas frases no YouTube
SEARCH_TERMS: list[str] = [
    "genius home hacks",
    "tech gadgets for home",
    "life hacks 2026",
    "useful life hacks",
    "cleaning tips",
    "gadget review",
    "satisfying cleaning",
    "amazon finds",
    "life hacks compilation",
]

# Quantos resultados buscar por termo de pesquisa
MAX_RESULTS_PER_TERM: int = 50

# Mínimo de visualizações para um vídeo ser considerado candidato
MIN_VIEWS: int = 20_000


# ─── Utilitários ──────────────────────────────────────────────────────────────

def get_cutoff_date() -> str:
    """
    Calcula a data de 7 dias atrás e retorna no formato YYYYMMDD.
    Usamos esse valor para filtrar apenas vídeos recentes.
    Exemplo: se hoje é 20260313, retorna '20260306'.
    """
    cutoff = datetime.now() - timedelta(days=7)
    return cutoff.strftime("%Y%m%d")


def load_existing_candidates() -> list[dict]:
    """
    Abre o arquivo raw_candidates.json e retorna os vídeos já salvos.
    Se o arquivo não existir ainda, retorna uma lista vazia sem travar.
    Isso permite que o script rode mesmo na primeira execução.
    """
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
    Salva O VÍDEO SELECIONADO (Top 1) no arquivo, substituindo a execução anterior.
    Garante que o pipeline (transformer, downloader) leia sempre apenas o vídeo da vez.
    """
    if not data:
        print("[INFO] Nenhum vídeo para salvar.")
        return

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[OK] Atualizado {OUTPUT_FILE} com o Top 1 vídeo.")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar candidatos: {e}")


# ─── Busca de Vídeos ──────────────────────────────────────────────────────────

def fetch_videos(search_query: str, max_results: int, min_views: int) -> list[dict]:
    """
    Pesquisa vídeos no YouTube usando o yt-dlp e aplica dois filtros:
      - Mínimo de visualizações (ex: 50.000 views)
      - Data de upload (apenas vídeos dos últimos 7 dias)

    Retorna uma lista de dicionários com os dados dos vídeos aprovados.
    """
    results: list[dict] = []

    # Calcula a data mínima para aceitar um vídeo (7 dias atrás)
    cutoff_date: str = get_cutoff_date()

    # Configurações do yt-dlp: modo silencioso e tolerante a erros
    ydl_opts: dict = {
        "extract_flat": False,  # Baixa todos os metadados, não apenas o básico
        "quiet": True,          # Não imprime logs técnicos no terminal
        "no_warnings": True,    # Ignora alertas de cookies, região, etc.
        "ignoreerrors": True,   # Se um vídeo falhar, continua para o próximo
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Monta a URL de busca: "ytsearch15:viral life hacks" busca 15 resultados
            search_url: str = f"ytsearch{max_results}:{search_query}"
            print(f"[BUSCANDO] '{search_query}'...")

            # Solicita os metadados dos vídeos sem baixar nada
            info = ydl.extract_info(search_url, download=False)

            # Verifica se veio algum resultado
            if not info or "entries" not in info:
                return results

            entries = info["entries"]
            if not isinstance(entries, list):
                return results

            # Analisa cada vídeo encontrado
            for entry in entries:
                if not entry or not isinstance(entry, dict):
                    continue

                try:
                    # Extrai os campos com casting explícito para evitar erros de tipo
                    video_id: str = str(entry.get("id", ""))
                    title: str = str(entry.get("title", ""))
                    url: str = str(entry.get("webpage_url", f"https://www.youtube.com/watch?v={video_id}"))

                    # view_count pode vir como None — usamos 0 como valor padrão seguro
                    view_count_raw = entry.get("view_count")
                    view_count: int = int(view_count_raw) if isinstance(view_count_raw, (int, float)) else 0

                    # upload_date vem no formato YYYYMMDD (ex: "20260310")
                    upload_date_raw: str = str(entry.get("upload_date", "")).strip()
                    upload_date: str = "".join(list(upload_date_raw)[:8]) if len(upload_date_raw) >= 8 else ""  # type: ignore

                    # ── Filtro 1: descarta vídeos com poucas visualizações ──
                    if view_count < min_views:
                        continue

                    # ── Filtro 2: descarta vídeos mais antigos que 7 dias ──
                    if not upload_date or upload_date < cutoff_date:
                        continue

                    # Vídeo passou nos dois filtros — adiciona à lista
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

def mine() -> str | None:
    """
    Orquestrador: busca vídeos para todos os termos, descarta duplicatas,
    ordena por view_count e seleciona apenas o TOP 1 absoluto para esta execução.
    Retorna o título processado (slug) se encontrou, caso contrário None.
    """
    all_new_videos: list[dict] = []
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
        # Padrão ADS: Ordena vídeos de forma decrescente por visualizações e pega o maior
        all_new_videos.sort(key=lambda x: x.get("view_count", 0), reverse=True)
        top_1_video = all_new_videos[0]
        
        print(f"\n[RESULTADO] TOP 1 Vídeo Encontrado: '{top_1_video.get('title')}' com {top_1_video.get('view_count')} views!")
        
        # Salva somento o top 1 como uma lista de 1 elemento no json
        save_to_json([top_1_video])
        return top_1_video.get('title')
    else:
        print("\n[RESULTADO] Nenhum vídeo novo passou nos filtros desta execução.")
        return None


if __name__ == "__main__":
    mine()
