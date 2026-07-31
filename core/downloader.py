# =====================================================================
# --- IMPORTS & DEPENDENCIES ---
# =====================================================================
import os
import time
import requests
import urllib.parse
import zipfile
import patoolib
import threading
import json

# Optional desktop notification support check
try:
    from plyer import notification
    HAS_NOTIFICATIONS = True
except ImportError:
    HAS_NOTIFICATIONS = False


# =====================================================================
# --- HISTORY FILE MANAGEMENT ---
# =====================================================================
HISTORY_FILE = "download_history.json"

def load_history():
    """Loads completed download history logs from disk[cite: 6]."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history_item(item):
    """Appends a completed download record to history storage[cite: 6]."""
    history = load_history()
    history.insert(0, item)
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"Error saving history: {e}")


# =====================================================================
# --- FILE DOWNLOAD & EXTRACTION ENGINE ---
# =====================================================================
class FileDownloader:
    def __init__(self):
        self.active_downloads = {}
        self.download_queue = []
        self.is_processing_queue = False
        self.queue_lock = threading.Lock()

    def add_to_queue(self, download_tasks, speed_limit=None, progress_callback=None, queue_complete_callback=None):
        """Appends multiple download links to the queue and starts processing worker[cite: 6]."""
        with self.queue_lock:
            for link in download_tasks:
                self.download_queue.append({
                    "url": link,
                    "speed_limit": speed_limit,
                    "progress_callback": progress_callback
                })
        
        self.queue_complete_callback = queue_complete_callback
        if not self.is_processing_queue:
            threading.Thread(target=self._process_queue_loop, daemon=True).start()

    def _process_queue_loop(self):
        """Worker loop that sequentially handles queued file downloads[cite: 6]."""
        self.is_processing_queue = True
        while True:
            with self.queue_lock:
                if not self.download_queue:
                    self.is_processing_queue = False
                    if self.queue_complete_callback:
                        self.queue_complete_callback()
                    break
                task = self.download_queue.pop(0)

            self.download_file(
                url=task["url"],
                speed_limit_mbps=task["speed_limit"],
                progress_callback=task["progress_callback"]
            )

    def download_file(self, url, save_folder="Downloads", speed_limit_mbps=None, progress_callback=None, download_id=None):
        """Downloads a single file with bandwidth shaping, progress updates, and auto-extraction[cite: 6]."""
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
            
        raw_filename = url.split('/')[-1].split('?')[0]
        local_filename = urllib.parse.unquote(raw_filename)
        if not local_filename:
            local_filename = "downloaded_file.bin"
            
        file_path = os.path.join(save_folder, local_filename)
        if not download_id:
            download_id = str(abs(hash(url)))

        bytes_per_sec = None
        if speed_limit_mbps and speed_limit_mbps > 0:
            bytes_per_sec = int((speed_limit_mbps * 1_000_000) / 8)

        self.active_downloads[download_id] = True
        target_open_path = file_path

        try:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                
                downloaded = 0
                start_time = time.time()
                chunk_size = 8192
                
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if not self.active_downloads.get(download_id, True):
                            return None
                        if not chunk:
                            continue
                            
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            percent = min(float(downloaded / total_size), 1.0)
                            elapsed = time.time() - start_time
                            speed_mbps = (downloaded * 8) / (elapsed * 1_000_000) if elapsed > 0 else 0
                            progress_callback(download_id, local_filename, percent, speed_mbps)
                        
                        if bytes_per_sec:
                            elapsed = time.time() - start_time
                            expected_time = downloaded / bytes_per_sec
                            if expected_time > elapsed:
                                time.sleep(expected_time - elapsed)
                                
            if progress_callback:
                progress_callback(download_id, local_filename, 1.0, 0)

            # Auto-Extract Utility & set target folder for history
            if file_path.lower().endswith(('.zip', '.rar', '.7z')):
                print(f"Auto-extracting archive: {local_filename}...")
                extract_folder = os.path.join(save_folder, os.path.splitext(local_filename)[0])
                os.makedirs(extract_folder, exist_ok=True)
                try:
                    if file_path.lower().endswith('.zip'):
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_folder)
                    else:
                        patoolib.extract_archive(file_path, outdir=extract_folder)
                    target_open_path = extract_folder
                    print(f"Extraction complete: {extract_folder}")
                except Exception as ex:
                    print(f"Extraction failed: {ex}")

            save_history_item({
                "filename": local_filename,
                "path": target_open_path,
                "date": time.strftime("%Y-%m-%d %H:%M:%S")
            })

            return file_path
        except Exception as e:
            print(f"Download error for {local_filename}: {e}")
            return None
        finally:
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]

    def stop_download(self, download_id):
        """Halts an active download thread[cite: 6]."""
        if download_id in self.active_downloads:
            self.active_downloads[download_id] = False

downloader_engine = FileDownloader()