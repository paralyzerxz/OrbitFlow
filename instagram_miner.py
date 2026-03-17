# instagram_miner.py
# ─────────────────────────────────────────────────────────────────────────────
# RESPONSABILIDADE: Mineração de vídeos do Instagram (Reels).
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
import time
import random
from datetime import datetime, timedelta
from typing import List
import instaloader # type: ignore

# ─── Configuração ─────────────────────────────────────────────────────────────

HASHTAGS: list[str] = [
    "homehacks",
    "amazonfinds",
    "usefulgadgets",
    "cleaninghacks",
    "lifehacks",
    "gadgets",
]

MIN_LIKES: int = 5_000

def get_cutoff_date() -> datetime:
    return datetime.now() - timedelta(days=7)

def mine() -> list[dict]:
    L = instaloader.Instaloader(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    results = []
    cutoff_date = get_cutoff_date()
    
    # Shuffle and pick few hashtags to avoid ban
    hashtags_to_check: List[str] = list(HASHTAGS)
    random.shuffle(hashtags_to_check)

    # Pegando apenas os 2 primeiros sem usar fatiamento [:]
    for i, tag_name in enumerate(hashtags_to_check):
        if i >= 2: break
        print(f"[INSTAGRAM] Buscando hashtag: #{tag_name}...")

        try:

            hashtag = instaloader.Hashtag.from_name(L.context, tag_name)
            posts = hashtag.get_posts()
            
            count = 0
            for post in posts:
                # Instaloader posts are usually chronological (desc)
                if post.date_utc < cutoff_date:
                    break # Reached old posts
                
                if post.is_video:
                    likes = post.likes
                    if likes >= MIN_LIKES:
                        results.append({
                            "id": post.shortcode,
                            "title": post.caption[:100].replace("\n", " ") if post.caption else f"Instagram Reel {post.shortcode}",
                            "url": f"https://www.instagram.com/reels/{post.shortcode}/",
                            "view_count": likes * 20, # Normalizing: Estimating views as ~20x likes for ranking
                            "platform": "instagram",
                            "likes": likes
                        })
                
                count += 1
                if count > 30: # Check max 30 recent posts per tag
                    break
                    
            # Delay between hashtags
            time.sleep(random.uniform(5, 10))
            
        except Exception as e:
            print(f"[INSTAGRAM ERROR] Erro na tag {tag_name}: {e}")
            if "401" in str(e) or "429" in str(e):
                print("[INSTAGRAM] Bloqueio ou Rate Limit detectado. Abortando Insta por agora.")
                break
                
    return results

if __name__ == "__main__":
    res = mine()
    print(f"Encontrados {len(res)} vídeos no Instagram.")
