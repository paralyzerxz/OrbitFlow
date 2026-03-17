# tiktok_miner.py
# ─────────────────────────────────────────────────────────────────────────────
# RESPONSABILIDADE: Mineração de vídeos do TikTok.
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
import time
import random
from datetime import datetime, timedelta
from typing import List
import yt_dlp # type: ignore

# ─── Configuração ─────────────────────────────────────────────────────────────

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

MAX_RESULTS_PER_TERM: int = 20
MIN_VIEWS: int = 50_000

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

def get_cutoff_date() -> datetime:
    return datetime.now() - timedelta(days=7)

def fetch_tiktok_videos(query: str) -> list[dict]:
    results = []
    cutoff_date = get_cutoff_date()
    
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "extract_flat": "in_playlist",
        "user_agent": random.choice(USER_AGENTS),
    }

    # TikTok search URL using yt-dlp's internal support or just the search results
    search_url = f"https://www.tiktok.com/search/video?q={query.replace(' ', '%20')}"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"[TIKTOK] Buscando: '{query}'...")
            # Pequeno delay para evitar blocos
            time.sleep(random.uniform(2, 5))
            
            # Usando o prefixo ytsearch que o yt-dlp suporta para várias plataformas
            # Para o TikTok, ele costuma funcionar com a URL de busca direta ou apenas o termo se configurado
            info = ydl.extract_info(f"https://www.tiktok.com/search?q={query}", download=False)
            
            if not info or "entries" not in info:
                return results

            for entry in info["entries"]:
                if not entry: continue
                
                view_count = entry.get("view_count", 0)
                if view_count < MIN_VIEWS:
                    continue
                
                # yt-dlp neither provides a clear timestamp for search entries on TikTok always
                # but we can try to estimate or skip if unavailable.
                # For this implementation, we assume yt-dlp's relevance sort helps.
                
                results.append({
                    "id": entry.get("id"),
                    "title": entry.get("title") or entry.get("description") or f"Tiktok video {entry.get('id')}",
                    "url": entry.get("url") or f"https://www.tiktok.com/@{entry.get('uploader')}/video/{entry.get('id')}",
                    "view_count": view_count,
                    "platform": "tiktok"
                })
    except Exception as e:
        print(f"[TIKTOK ERROR] {e}")
        
    return results

def mine() -> list[dict]:
    all_videos = []
    seen_ids = set()
    
    # Shuffle terms to vary results
    terms_to_check = list(SEARCH_TERMS)
    random.shuffle(terms_to_check)

    # Pegando apenas os 3 primeiros sem usar fatiamento [:]
    for i, term in enumerate(terms_to_check):
        if i >= 3: break
        videos = fetch_tiktok_videos(term)
        for v in videos:
            if v["id"] not in seen_ids:
                all_videos.append(v)
                seen_ids.add(v["id"])
        
        # Inter-term sleep
        time.sleep(random.uniform(5, 10))
        
    return all_videos

if __name__ == "__main__":
    res = mine()
    print(f"Encontrados {len(res)} vídeos no TikTok.")
