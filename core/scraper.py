# =====================================================================
# --- IMPORTS & DEPENDENCIES ---
# =====================================================================
import os
import html
import json
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed


# =====================================================================
# --- CONFIGURATION & ENDPOINTS ---
# =====================================================================
_BASE_URL = "https://fitgirl-repacks.site"
_API_URL = f"{_BASE_URL}/wp-json/wp/v2/posts"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
_CACHE_FILE = "repacks_cache.json"
_POPULAR_CACHE_FILE = "popular_cache.json"


# =====================================================================
# --- SEARCH API SCRAPER ---
# =====================================================================
def search_fitgirl_api(query):
    """Searches FitGirl via WordPress REST API and extracts magnet links directly[cite: 5]."""
    params = {
        "search": query,
        "per_page": 5
    }
    
    try:
        response = requests.get(_API_URL, params=params, headers=_HEADERS, timeout=15)
        response.raise_for_status()
        posts = response.json()
        
        results = []
        for post in posts:
            raw_title = post.get('title', {}).get('rendered', '').strip()
            title = html.unescape(raw_title)
            content_html = post.get('content', {}).get('rendered', '')
            
            soup = BeautifulSoup(content_html, 'html.parser')
            
            magnet_link = None
            for a in soup.find_all('a', href=True):
                if a['href'].startswith('magnet:'):
                    magnet_link = a['href']
                    break
                    
            img_url = None
            img_tag = soup.find('img')
            if img_tag:
                img_url = img_tag.get('src') or img_tag.get('data-src') or img_tag.get('data-lazy-src')
            
            if magnet_link:
                results.append({
                    "title": title,
                    "magnet": magnet_link,
                    "image": img_url,
                    "url": post.get('link')
                })
                
        return results
    except Exception as e:
        print(f"Error fetching from FitGirl API: {e}")
        return []


# =====================================================================
# --- CACHE MANAGEMENT & RECENT POSTS ---
# =====================================================================
def get_cached_posts_only():
    """Instantly returns local cache without touching the network[cite: 5]."""
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def fetch_and_update_cache():
    """Fetches fresh posts from the API in the background and updates the local cache[cite: 5]."""
    params = {
        "per_page": 30
    }
    try:
        response = requests.get(_API_URL, params=params, headers=_HEADERS, timeout=15)
        response.raise_for_status()
        posts = response.json()
        
        results = []
        for post in posts:
            raw_title = post.get('title', {}).get('rendered', '').strip()
            title = html.unescape(raw_title)
            
            lower_title = title.lower()
            if "updates digest" in lower_title or "repack roundup" in lower_title or "site update" in lower_title:
                continue
                
            content_html = post.get('content', {}).get('rendered', '')
            soup = BeautifulSoup(content_html, 'html.parser')
            
            magnet_link = None
            for a in soup.find_all('a', href=True):
                if a['href'].startswith('magnet:'):
                    magnet_link = a['href']
                    break
                
            img_url = None
            img_tag = soup.find('img')
            if img_tag:
                img_url = img_tag.get('src') or img_tag.get('data-src') or img_tag.get('data-lazy-src')

            if title and magnet_link:
                results.append({
                    "title": title,
                    "magnet": magnet_link,
                    "image": img_url,
                    "url": post.get('link')
                })
                
            if len(results) >= 24:
                break
                
        if results:
            with open(_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
        return results
    except Exception:
        return []

def get_recent_fitgirl_posts(force_refresh=False):
    """Loads cache instantly, or fetches live if force_refresh is True[cite: 5]."""
    if force_refresh:
        fresh = fetch_and_update_cache()
        if fresh:
            return fresh

    cached = get_cached_posts_only()
    if not cached:
        return fetch_and_update_cache()
    else:
        import threading
        threading.Thread(target=fetch_and_update_cache, daemon=True).start()
    return cached


# =====================================================================
# --- POPULAR REPACKS SCRAPER ---
# =====================================================================
def get_popular_repacks(force_refresh=False):
    """Loads popular repacks from cache instantly, or scrapes live if force_refresh is True[cite: 5]."""
    if not force_refresh and os.path.exists(_POPULAR_CACHE_FILE):
        try:
            with open(_POPULAR_CACHE_FILE, "r", encoding="utf-8") as f:
                cached_popular = json.load(f)
                if cached_popular:
                    import threading
                    threading.Thread(target=_fetch_and_cache_popular, daemon=True).start()
                    return cached_popular
        except Exception:
            pass

    return _fetch_and_cache_popular()

def _fetch_and_cache_popular():
    """Scrapes the popular widget and saves it to local cache[cite: 5]."""
    try:
        response = requests.get(_BASE_URL, headers=_HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        target_items = []
        
        for widget in soup.select('.jetpack_top_posts_widget'):
            widget_title = widget.find(['h2', 'h3', 'h4'])
            if widget_title and "Most Popular Repacks of the Week" in widget_title.get_text():
                for item_div in widget.select('.widget-grid-view-image'):
                    a_tag = item_div.find('a', href=True)
                    if not a_tag:
                        continue
                        
                    game_url = a_tag.get('href')
                    raw_title = a_tag.get('title') or ""
                    
                    img_tag = a_tag.find('img')
                    img_url = None
                    if img_tag:
                        img_url = img_tag.get('src') or img_tag.get('data-src')
                        
                    if game_url and raw_title:
                        target_items.append({
                            "url": game_url,
                            "title": html.unescape(raw_title),
                            "image": img_url
                        })
                break

        if not target_items:
            widget = soup.select_one('.jetpack_top_posts_widget')
            if widget:
                for item_div in widget.select('.widget-grid-view-image'):
                    a_tag = item_div.find('a', href=True)
                    if not a_tag:
                        continue
                    game_url = a_tag.get('href')
                    raw_title = a_tag.get('title') or ""
                    img_tag = a_tag.find('img')
                    img_url = img_tag.get('src') if img_tag else None
                    
                    if game_url and raw_title:
                        target_items.append({
                            "url": game_url,
                            "title": html.unescape(raw_title),
                            "image": img_url
                        })

        results = []

        def fetch_popular_magnet(item):
            try:
                game_resp = requests.get(item["url"], headers=_HEADERS, timeout=8)
                if game_resp.status_code == 200:
                    game_soup = BeautifulSoup(game_resp.text, 'html.parser')
                    for link in game_soup.find_all('a', href=True):
                        if link['href'].startswith('magnet:'):
                            return {
                                "title": item["title"],
                                "magnet": link['href'],
                                "image": item["image"],
                                "url": item["url"]
                            }
            except Exception:
                pass
            return None

        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_item = {executor.submit(fetch_popular_magnet, item): item for item in target_items}
            for future in as_completed(future_to_item):
                res = future.result()
                if res:
                    results.append(res)

        if results:
            try:
                with open(_POPULAR_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=4)
            except Exception:
                pass
                
        return results
    except Exception as e:
        print(f"Error scraping popular repacks: {e}")
        if os.path.exists(_POPULAR_CACHE_FILE):
            try:
                with open(_POPULAR_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []


# =====================================================================
# --- UPCOMING REPACKS & SCHEDULE SCRAPER ---
# =====================================================================
def get_upcoming_repacks():
    """Scrapes FitGirl's upcoming repacks from the colored span layout[cite: 5]."""
    upcoming_url = "https://fitgirl-repacks.site/upcoming-repacks/"
    try:
        response = requests.get(upcoming_url, headers=_HEADERS, timeout=10)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        upcoming_items = []
        for span in soup.find_all('span', style=lambda value: value and '#339966' in value.lower()):
            text = span.get_text().strip()
            if text and len(text) > 2:
                if {"title": text, "magnet": None, "image": None} not in upcoming_items:
                    upcoming_items.append({
                        "title": text,
                        "magnet": None,
                        "image": None
                    })
                    
        return upcoming_items[:50]
    except Exception as e:
        print(f"Error fetching upcoming repacks: {e}")
        return []

def search_upcoming_fallback():
    """Fallback to searching posts if the exact slug endpoint varies[cite: 5]."""
    try:
        response = requests.get(f"{_BASE_URL}/upcoming-repacks/", headers=_HEADERS, timeout=10)
        if response.status_code != 200:
            return [{"title": "Could not connect to upcoming schedule page.", "magnet": None, "image": None}]
            
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.select_one('.entry-content')
        
        items = []
        if content_div:
            for element in content_div.find_all(['li', 'p']):
                text = element.get_text().strip()
                lower_text = text.lower()
                if not text or len(text) < 4 or "do not ask" in lower_text or "p.s." in lower_text:
                    continue
                items.append({
                    "title": text,
                    "magnet": None,
                    "image": None
                })
        return items[:40]
    except Exception:
        return []


# =====================================================================
# --- SITE STATUS CHECKER ---
# =====================================================================
def check_site_status():
    """Checks if FitGirl Repacks site is up and reachable[cite: 5]."""
    try:
        response = requests.get(_BASE_URL, headers=_HEADERS, timeout=5)
        return response.status_code == 200
    except Exception:
        return False