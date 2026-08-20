import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import requests
import json
from bs4 import BeautifulSoup
import re

from debrid_api import get_user_account_info, add_magnet_get_info, confirm_files_selection
from scraper import search_fitgirl_api, get_recent_fitgirl_posts, get_popular_repacks, get_upcoming_repacks, check_site_status
from downloader import downloader_engine, load_history, HISTORY_FILE

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SteamGridDB API Configuration
STEAMGRIDDB_API_KEY = "14dcdc5f391a009fc1ec64ea466372f2"

class TorrentInfoRequest(BaseModel):
    magnet: str = ""
    api_key: str

class TorrentSelectRequest(BaseModel):
    torrent_id: str
    selected_files: list
    api_key: str
    speed_limit: float = None
    image: str = ""

class SearchRequest(BaseModel):
    query: str

class DetailsRequest(BaseModel):
    url: str

class SpeedLimitRequest(BaseModel):
    speed_limit: float

class ControlRequest(BaseModel):
    download_id: str

class HistoryActionRequest(BaseModel):
    path: str = ""
    index: int = None

class BannerRequest(BaseModel):
    title: str

def fetch_steamgriddb_banner(raw_title: str) -> str:
    """Helper to automatically clean title and fetch banner from SteamGridDB"""
    if not raw_title:
        return ""
    
    clean_title = re.sub(r'\[.*?\]', '', raw_title)
    clean_title = re.sub(r'\(.*?\)', '', clean_title)
    clean_title = re.sub(r'\.(rar|zip|exe|7z)$', '', clean_title, flags=re.IGNORECASE).strip()
    
    headers = {"Authorization": f"Bearer {STEAMGRIDDB_API_KEY}"}
    try:
        search_res = requests.get(f"https://www.steamgriddb.com/api/v2/search/autocomplete/{clean_title}", headers=headers, timeout=5)
        search_data = search_res.json()
        if search_data.get("success") and search_data.get("data"):
            game_id = search_data["data"][0]["id"]
            banners_res = requests.get(f"https://www.steamgriddb.com/api/v2/heroes/game/{game_id}", headers=headers, timeout=5)
            banners_data = banners_res.json()
            if banners_data.get("success") and banners_data.get("data"):
                return banners_data["data"][0]["url"]
    except Exception as e:
        print(f"SteamGridDB automatic fetch error: {e}")
    return ""

@app.get("/api/status")
def get_status():
    return {"site_up": check_site_status()}

@app.post("/api/account")
def get_account(req: TorrentInfoRequest):
    try:
        account_data = get_user_account_info(req.api_key)
        if account_data and 'type' in account_data:
            return {"active": True, "type": account_data.get('type')}
        raise HTTPException(status_code=400, detail="Invalid API Key")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/recent")
def get_recent(page: int = Query(1), force: bool = Query(False)):
    return get_recent_fitgirl_posts(page=page, force_refresh=force)

@app.get("/api/popular")
def get_popular(force: bool = Query(False)):
    return get_popular_repacks(force_refresh=force)

@app.get("/api/upcoming")
def get_upcoming():
    return get_upcoming_repacks()

@app.post("/api/search")
def search_games(payload: SearchRequest):
    return search_fitgirl_api(payload.query)

@app.post("/api/banner")
async def get_game_banner(req: BannerRequest):
    banner_url = fetch_steamgriddb_banner(req.title)
    if banner_url:
        return {"banner_url": banner_url}
    raise HTTPException(status_code=404, detail="Banner not found")

@app.post("/api/speed")
def set_speed_limit(payload: SpeedLimitRequest):
    try:
        if hasattr(downloader_engine, 'update_speed_limit'):
            downloader_engine.update_speed_limit(payload.speed_limit)
        return {"success": True, "speed_limit": payload.speed_limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/torrent/info")
def get_torrent_info(req: TorrentInfoRequest):
    try:
        if not req.api_key:
            raise HTTPException(status_code=400, detail="API Key is missing.")
        if not req.magnet:
            raise HTTPException(status_code=400, detail="Magnet link is missing.")
            
        torrent_info = add_magnet_get_info(req.magnet, req.api_key)
        if not torrent_info:
            raise HTTPException(status_code=400, detail="Failed to fetch torrent info from Real-Debrid")
            
        filename = torrent_info.get("filename", "")
        banner_url = fetch_steamgriddb_banner(filename)
        if banner_url:
            torrent_info["banner_url"] = banner_url
            
        return torrent_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/torrent/select")
def select_torrent_files(req: TorrentSelectRequest):
    try:
        download_links = confirm_files_selection(req.torrent_id, req.selected_files, req.api_key)
        if not download_links:
            raise HTTPException(status_code=400, detail="Failed to confirm file selection")
            
        tasks_with_meta = [{"url": link, "image": req.image} for link in download_links]
            
        downloader_engine.add_to_queue(
            download_tasks=tasks_with_meta,
            speed_limit=req.speed_limit,
            progress_callback=lambda did, fn, prog, spd, eta: None,
            queue_complete_callback=lambda: None
        )
        return {"success": True, "links": download_links}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/downloads/active")
def get_active_downloads():
    if hasattr(downloader_engine, 'get_active_downloads_status'):
        return downloader_engine.get_active_downloads_status()
    return {}

@app.post("/api/downloads/pause")
def pause_download(req: ControlRequest):
    downloader_engine.pause_download(req.download_id)
    return {"success": True}

@app.post("/api/downloads/resume")
def resume_download(req: ControlRequest):
    downloader_engine.resume_download(req.download_id)
    return {"success": True}

@app.post("/api/downloads/stop")
def stop_download(req: ControlRequest):
    downloader_engine.stop_download(req.download_id)
    return {"success": True}

@app.get("/api/history")
def get_history():
    return load_history()

@app.post("/api/history/open")
def open_history_folder(req: HistoryActionRequest):
    try:
        if req.path and os.path.exists(req.path):
            os.startfile(os.path.abspath(req.path))
            return {"success": True}
        raise HTTPException(status_code=404, detail="Path not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/history/delete")
def delete_history_item(req: HistoryActionRequest):
    try:
        history = load_history()
        if req.index is not None and 0 <= req.index < len(history):
            history.pop(req.index)
            with open(HISTORY_FILE, "w") as f:
                json.dump(history, f, indent=4)
            return {"success": True, "history": history}
        raise HTTPException(status_code=400, detail="Invalid index")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/details")
def get_game_details(req: DetailsRequest):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', "Referer": "https://fitgirl-repacks.site/"}
        target_url = req.url
        if not target_url:
            raise HTTPException(status_code=400, detail="URL is missing")

        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Failed to load page")
            
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.find('div', class_='entry-content')
        
        if not content_div:
            return {"items": [{"type": "text", "content": "No details found."}]}
            
        for tag in content_div.find_all(['style', 'script']):
            tag.decompose()

        parsed_items = []
        
        first_p = content_div.find('p')
        if first_p:
            img = first_p.find('img')
            if img:
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    parsed_items.append({'type': 'image', 'url': img_url})
            for img_tag in first_p.find_all('img'):
                img_tag.decompose()
            meta_text = first_p.get_text().strip()
            if meta_text:
                parsed_items.append({'type': 'text', 'content': meta_text})

        screenshots_header = None
        for h3 in content_div.find_all('h3'):
            if 'screenshots' in h3.get_text().lower():
                screenshots_header = h3
                break
        
        if screenshots_header:
            parsed_items.append({'type': 'text', 'content': "Screenshots:"})
            curr = screenshots_header.find_next_sibling()
            while curr and curr.name != 'h3':
                if curr.name in ['p', 'div']:
                    for img in curr.find_all('img'):
                        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                        if img_url and not any(bad in img_url.lower() for bad in ['support2', 'cropped-icon', 'paw.png']):
                            parsed_items.append({'type': 'image', 'url': img_url})
                curr = curr.find_next_sibling()

        features_header = None
        for h3 in content_div.find_all('h3'):
            if 'repack features' in h3.get_text().lower():
                features_header = h3
                break
        
        if features_header:
            parsed_items.append({'type': 'text', 'content': "Repack Features:"})
            ul_elem = features_header.find_next_sibling('ul')
            if ul_elem:
                seen_items = set()
                for li in ul_elem.find_all('li', recursive=False):
                    li_text = li.get_text().strip()
                    if li_text and li_text not in seen_items:
                        seen_items.add(li_text)
                        parsed_items.append({'type': 'text', 'content': f"• {li_text}"})

        spoiler_content = None
        for spoiler in content_div.find_all('div', class_='su-spoiler'):
            title_div = spoiler.find('div', class_='su-spoiler-title')
            if title_div and 'game description' in title_div.get_text().lower():
                spoiler_content = spoiler.find('div', class_='su-spoiler-content')
                break

        if spoiler_content:
            parsed_items.append({'type': 'text', 'content': "Game Description:"})
            clean_desc = spoiler_content.get_text(separator=" ", strip=True)
            if clean_desc:
                parsed_items.append({'type': 'text', 'content': clean_desc})

        if len(parsed_items) <= 1 or not features_header:
            parsed_items = [
                parsed_items[0] if parsed_items else {'type': 'text', 'content': "Release Details"},
                {
                    'type': 'text', 
                    'content': (
                        "Detailed text description unavailable for this release format due to how it is set up. "
                        "You can find it directly on the website.\n\n"
                        "Use the download button below to grab the torrent directly via Real-Debrid."
                    )
                }
            ]

        return {"items": parsed_items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Custom log config with no console dependencies to fix PyInstaller --noconsole
    custom_log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "default": {
                "class": "logging.NullHandler",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO"},
        },
    }
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=custom_log_config)