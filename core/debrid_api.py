# =====================================================================
# --- IMPORTS & DEPENDENCIES ---
# =====================================================================
import os
import time
import requests
from dotenv import load_dotenv


# =====================================================================
# --- HEADER & AUTHENTICATION UTILITIES ---
# =====================================================================
def get_headers(custom_api_key=None):
    """Generates authorization headers using custom key or environment variables[cite: 7]."""
    key = custom_api_key or os.getenv("RD_API_KEY")
    return {"Authorization": f"Bearer {key}"}

_API_BASE = "https://api.real-debrid.com/rest/1.0"


# =====================================================================
# --- REAL-DEBRID ACCOUNT API ---
# =====================================================================
def get_user_account_info(custom_api_key=None):
    """Fetches user account status, type, and expiration days[cite: 7]."""
    url = f"{_API_BASE}/user"
    try:
        response = requests.get(url, headers=get_headers(custom_api_key), timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching account info: {e}")
    return None


# =====================================================================
# --- TORRENT SUBMISSION & FILE MANAGEMENT API ---
# =====================================================================
def add_magnet_get_info(magnet_link, custom_api_key=None):
    """Adds the magnet link to Real-Debrid and fetches the file list[cite: 7]."""
    print("Sending magnet to Real-Debrid...")
    
    add_url = f"{_API_BASE}/torrents/addMagnet"
    response = requests.post(add_url, headers=get_headers(custom_api_key), data={"magnet": magnet_link})
    
    if response.status_code not in [200, 201]:
        print(f"Error adding magnet: {response.text}")
        return None
        
    data = response.json()
    torrent_id = data.get("id")
    if not torrent_id:
        return None
        
    info_url = f"{_API_BASE}/torrents/info/{torrent_id}"
    info_resp = requests.get(info_url, headers=get_headers(custom_api_key))
    
    if info_resp.status_code == 200:
        info_data = info_resp.json()
        return {
            "id": torrent_id,
            "filename": info_data.get("filename", "Unknown Torrent"),
            "files": info_data.get("files", [])
        }
        
    return None

def confirm_files_selection(torrent_id, selected_file_ids, custom_api_key=None):
    """Submits file selection and mirrors the web UI's torrent lifecycle[cite: 7]."""
    select_url = f"{_API_BASE}/torrents/selectFiles/{torrent_id}"
    files_str = ",".join(map(str, selected_file_ids)) if selected_file_ids else "none"
    
    select_resp = requests.post(select_url, headers=get_headers(custom_api_key), data={"files": files_str})
    if select_resp.status_code not in [200, 204]:
        print("Error: Failed to submit file selection to Real-Debrid.")
        return []

    info_url = f"{_API_BASE}/torrents/info/{torrent_id}"
    print("Torrent active in Real-Debrid cloud. Waiting for completion...")
    
    rd_links = []
    while True:
        info_resp = requests.get(info_url, headers=get_headers(custom_api_key)).json()
        status = info_resp.get('status')
        
        if status == 'downloaded':
            rd_links = info_resp.get('links', [])
            break
        elif status in ['error', 'dead', 'virus']:
            print(f"Error: Torrent failed on Real-Debrid side (Status: {status}).")
            return []
            
        time.sleep(2)

    print(f"Found {len(rd_links)} files. Unrestricting links...")
    unrestrict_url = f"{_API_BASE}/unrestrict/link"
    direct_urls = []
    
    for link in rd_links:
        unrestricted = requests.post(unrestrict_url, headers=get_headers(custom_api_key), data={"link": link}).json()
        if 'download' in unrestricted:
            direct_urls.append(unrestricted['download'])
            
    return direct_urls