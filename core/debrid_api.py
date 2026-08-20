import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.real-debrid.com/rest/1.0"


def get_headers(custom_api_key: str = None) -> dict:
    """Generate authorization headers using a custom key or environment variables."""
    key = custom_api_key or os.getenv("RD_API_KEY")
    return {"Authorization": f"Bearer {key}"}


def get_user_account_info(custom_api_key: str = None) -> dict:
    """Fetch user account status, profile type, and subscription details."""
    url = f"{API_BASE}/user"
    try:
        response = requests.get(url, headers=get_headers(custom_api_key), timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching account info: {e}")
    return None


def add_magnet_get_info(magnet_link: str, custom_api_key: str = None) -> dict:
    """Submit magnet link to Real-Debrid and retrieve parsed manifest file list."""
    add_url = f"{API_BASE}/torrents/addMagnet"
    response = requests.post(add_url, headers=get_headers(custom_api_key), data={"magnet": magnet_link})
    
    if response.status_code not in [200, 201]:
        print(f"Error adding magnet link: {response.text}")
        return None
        
    data = response.json()
    torrent_id = data.get("id")
    if not torrent_id:
        return None
        
    info_url = f"{API_BASE}/torrents/info/{torrent_id}"
    info_resp = requests.get(info_url, headers=get_headers(custom_api_key))
    
    if info_resp.status_code == 200:
        info_data = info_resp.json()
        return {
            "id": torrent_id,
            "filename": info_data.get("filename", "Unknown Torrent"),
            "files": info_data.get("files", [])
        }
        
    return None


def confirm_files_selection(torrent_id: str, selected_file_ids: list, custom_api_key: str = None) -> list:
    """Submit targeted file selection, wait for cloud download, and unrestrict direct links."""
    select_url = f"{API_BASE}/torrents/selectFiles/{torrent_id}"
    files_str = ",".join(map(str, selected_file_ids)) if selected_file_ids else "none"
    
    select_resp = requests.post(select_url, headers=get_headers(custom_api_key), data={"files": files_str})
    if select_resp.status_code not in [200, 204]:
        print("Error: Failed to submit file selection mapping to Real-Debrid.")
        return []

    info_url = f"{API_BASE}/torrents/info/{torrent_id}"
    rd_links = []
    
    while True:
        try:
            info_resp = requests.get(info_url, headers=get_headers(custom_api_key), timeout=10).json()
            status = info_resp.get('status')
            
            if status == 'downloaded':
                rd_links = info_resp.get('links', [])
                break
            elif status in ['error', 'dead', 'virus']:
                print(f"Error: Torrent processing failed on cloud side (Status: {status}).")
                return []
        except Exception as e:
            print(f"Polling error: {e}")
            
        time.sleep(2)

    unrestrict_url = f"{API_BASE}/unrestrict/link"
    direct_urls = []
    
    for link in rd_links:
        try:
            unrestricted = requests.post(unrestrict_url, headers=get_headers(custom_api_key), data={"link": link}, timeout=10).json()
            if 'download' in unrestricted:
                direct_urls.append(unrestricted['download'])
        except Exception as e:
            print(f"Error unrestricting link: {e}")
            
    return direct_urls