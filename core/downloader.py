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
    """Loads completed download history logs from disk."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history_item(item):
    """Appends a completed download record to history storage."""
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
        self.paused_downloads = {}
        self.pause_events = {}
        self.speed_limit_mbps = None
        self.pause_start_times = {}
        self.total_paused_durations = {}
        self.speed_adjustment_baselines = {}

    def add_to_queue(self, download_tasks, speed_limit=None, progress_callback=None, queue_complete_callback=None):
        """Appends multiple download links to the queue and starts processing worker."""
        if speed_limit is not None:
            self.speed_limit_mbps = speed_limit

        with self.queue_lock:
            for link in download_tasks:
                self.download_queue.append({
                    "url": link,
                    "progress_callback": progress_callback
                })
        
        self.queue_complete_callback = queue_complete_callback
        if not self.is_processing_queue:
            threading.Thread(target=self._process_queue_loop, daemon=True).start()

    def _process_queue_loop(self):
        """Worker loop that sequentially handles queued file downloads."""
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
                progress_callback=task["progress_callback"]
            )

    def pause_download(self, download_id):
        """Pauses an active download thread."""
        if download_id in self.active_downloads:
            self.paused_downloads[download_id] = True
            self.pause_start_times[download_id] = time.time()
            if download_id in self.pause_events:
                self.pause_events[download_id].clear()

    def resume_download(self, download_id):
        """Resumes a paused download thread and adjusts pause duration offsets."""
        if download_id in self.active_downloads:
            self.paused_downloads[download_id] = False
            
            if download_id in self.pause_start_times:
                paused_duration = time.time() - self.pause_start_times[download_id]
                self.total_paused_durations[download_id] = self.total_paused_durations.get(download_id, 0.0) + paused_duration
                
            if download_id in self.pause_events:
                self.pause_events[download_id].set()

    def download_file(self, url, save_folder="Downloads", progress_callback=None, download_id=None):
        """Downloads a single file with dynamic bandwidth shaping, progress updates, and auto-extraction."""
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
            
        raw_filename = url.split('/')[-1].split('?')[0]
        local_filename = urllib.parse.unquote(raw_filename)
        if not local_filename:
            local_filename = "downloaded_file.bin"
            
        file_path = os.path.join(save_folder, local_filename)
        if not download_id:
            download_id = str(abs(hash(url)))

        self.active_downloads[download_id] = True
        
        # Setup pause event tracking
        pause_event = threading.Event()
        pause_event.set()
        self.pause_events[download_id] = pause_event
        self.paused_downloads[download_id] = False
        self.total_paused_durations[download_id] = 0.0
        self.speed_adjustment_baselines[download_id] = False

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
                            
                        # Respect pause state
                        pause_event.wait()

                        if not chunk:
                            continue
                            
                        # --- Dynamic On-The-Fly Speed Shaping Timing Reset (Preserves Progress) ---
                        if self.speed_adjustment_baselines.get(download_id, False):
                            # Reset start time and pause duration relative to current downloaded bytes
                            self.total_paused_durations[download_id] = 0.0
                            start_time = time.time()
                            if self.speed_limit_mbps and self.speed_limit_mbps > 0:
                                bytes_per_sec = int((self.speed_limit_mbps * 1_000_000) / 8)
                                if bytes_per_sec > 0:
                                    # Anchor start_time back so elapsed time accurately reflects the new speed limit rate
                                    start_time = time.time() - (downloaded / bytes_per_sec)
                            self.speed_adjustment_baselines[download_id] = False

                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Calculate elapsed time accurately by subtracting total pause durations
                        paused_offset = self.total_paused_durations.get(download_id, 0.0)
                        elapsed = (time.time() - start_time) - paused_offset
                        if elapsed <= 0:
                            elapsed = 0.001

                        if progress_callback and total_size > 0:
                            percent = min(float(downloaded / total_size), 1.0)
                            speed_mbps = (downloaded * 8) / (elapsed * 1_000_000) if elapsed > 0 else 0
                            
                            # --- Accurate ETA Calculation ---
                            eta_seconds = 0
                            if speed_mbps > 0:
                                remaining_bytes = total_size - downloaded
                                remaining_bits = remaining_bytes * 8
                                speed_bps = speed_mbps * 1_000_000
                                eta_seconds = int(remaining_bits / speed_bps)

                            progress_callback(download_id, local_filename, percent, speed_mbps, eta_seconds)
                        
                        # --- Dynamic On-The-Fly Speed Shaping Sleep ---
                        if self.speed_limit_mbps and self.speed_limit_mbps > 0:
                            bytes_per_sec = int((self.speed_limit_mbps * 1_000_000) / 8)
                            expected_time = downloaded / bytes_per_sec if bytes_per_sec > 0 else 0
                            if expected_time > elapsed:
                                time.sleep(expected_time - elapsed)
                                
            if progress_callback:
                progress_callback(download_id, local_filename, 1.0, 0, 0)

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
            if download_id in self.pause_events:
                del self.pause_events[download_id]
            if download_id in self.paused_downloads:
                del self.paused_downloads[download_id]
            if download_id in self.total_paused_durations:
                del self.total_paused_durations[download_id]
            if download_id in self.speed_adjustment_baselines:
                del self.speed_adjustment_baselines[download_id]

    def stop_download(self, download_id):
        """Halts an active download thread."""
        if download_id in self.active_downloads:
            self.active_downloads[download_id] = False
            if download_id in self.pause_events:
                self.pause_events[download_id].set()

    def update_speed_limit(self, new_limit):
        """Dynamically updates the speed limit and triggers baseline timer adjustment for active downloads."""
        self.speed_limit_mbps = new_limit
        for download_id in self.active_downloads.keys():
            self.speed_adjustment_baselines[download_id] = True

downloader_engine = FileDownloader()