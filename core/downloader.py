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


HISTORY_FILE = "download_history.json"


def load_history():
    """Load completed download history logs from disk safely."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history_item(item: dict):
    """Prepend a completed download record to history storage."""
    history = load_history()
    history.insert(0, item)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"Error saving history log: {e}")


class FileDownloader:
    def __init__(self):
        self.active_downloads = {}
        self.active_downloads_status = {}
        self.download_queue = []
        self.is_processing_queue = False
        self.queue_lock = threading.Lock()
        self.paused_downloads = {}
        self.pause_events = {}
        self.speed_limit_mbps = None
        self.pause_start_times = {}
        self.total_paused_durations = {}
        self.speed_adjustment_baselines = {}
        self.queue_complete_callback = None

    def add_to_queue(self, download_tasks, speed_limit: float = None, progress_callback=None, queue_complete_callback=None):
        """Append multiple download links to the queue and spawn worker processing."""
        if speed_limit is not None:
            self.speed_limit_mbps = speed_limit

        with self.queue_lock:
            for task_item in download_tasks:
                if isinstance(task_item, dict):
                    self.download_queue.append({
                        "url": task_item.get("url"),
                        "image": task_item.get("image", ""),
                        "progress_callback": progress_callback
                    })
                else:
                    self.download_queue.append({
                        "url": task_item,
                        "image": "",
                        "progress_callback": progress_callback
                    })
        
        self.queue_complete_callback = queue_complete_callback
        if not self.is_processing_queue:
            threading.Thread(target=self._process_queue_loop, daemon=True).start()

    def _process_queue_loop(self):
        """Sequential worker loop handling queued file download operations."""
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
                image=task.get("image", ""),
                progress_callback=task["progress_callback"]
            )

    def pause_download(self, download_id: str):
        """Pause an active download thread state."""
        if download_id in self.active_downloads:
            self.paused_downloads[download_id] = True
            self.pause_start_times[download_id] = time.time()
            if download_id in self.pause_events:
                self.pause_events[download_id].clear()
            if download_id in self.active_downloads_status:
                self.active_downloads_status[download_id]["status"] = "paused"

    def resume_download(self, download_id: str):
        """Resume a paused download thread and adjust duration offset tracking."""
        if download_id in self.active_downloads:
            self.paused_downloads[download_id] = False
            
            if download_id in self.pause_start_times:
                paused_duration = time.time() - self.pause_start_times[download_id]
                self.total_paused_durations[download_id] = self.total_paused_durations.get(download_id, 0.0) + paused_duration
                
            if download_id in self.pause_events:
                self.pause_events[download_id].set()
            if download_id in self.active_downloads_status:
                self.active_downloads_status[download_id]["status"] = "downloading"

    def download_file(self, url: str, save_folder: str = "Downloads", progress_callback=None, download_id: str = None, image: str = ""):
        """Download a single stream with bandwidth throttling, progress metrics, and auto-extraction."""
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
            
        raw_filename = url.split('/')[-1].split('?')[0]
        local_filename = urllib.parse.unquote(raw_filename) or "downloaded_file.bin"
            
        file_path = os.path.join(save_folder, local_filename)
        if not download_id:
            download_id = str(abs(hash(url)))

        self.active_downloads[download_id] = True
        self.active_downloads_status[download_id] = {
            "filename": local_filename,
            "image": image,
            "progress": 0.0,
            "speed": 0.0,
            "eta": 0,
            "status": "downloading"
        }
        
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
                    chunk_start_time = time.time()
                    chunk_bytes_downloaded = 0
                    speed_mbps = 0.0

                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if not self.active_downloads.get(download_id, True):
                            return None
                            
                        pause_event.wait()

                        if not chunk:
                            continue
                            
                        if self.speed_adjustment_baselines.get(download_id, False):
                            self.total_paused_durations[download_id] = 0.0
                            start_time = time.time()
                            if self.speed_limit_mbps and self.speed_limit_mbps > 0:
                                bytes_per_sec = int((self.speed_limit_mbps * 1_000_000) / 8)
                                if bytes_per_sec > 0:
                                    start_time = time.time() - (downloaded / bytes_per_sec)
                            self.speed_adjustment_baselines[download_id] = False
                            chunk_start_time = time.time()
                            chunk_bytes_downloaded = 0

                        f.write(chunk)
                        downloaded += len(chunk)
                        chunk_bytes_downloaded += len(chunk)
                        
                        now = time.time()
                        chunk_elapsed = now - chunk_start_time

                        if chunk_elapsed >= 0.5:
                            speed_mbps = (chunk_bytes_downloaded * 8) / (chunk_elapsed * 1_000_000)
                            chunk_start_time = now
                            chunk_bytes_downloaded = 0

                        paused_offset = self.total_paused_durations.get(download_id, 0.0)
                        total_elapsed = max((now - start_time) - paused_offset, 0.001)

                        percent = min(float(downloaded / total_size), 1.0) if total_size > 0 else 0.0
                        
                        eta_seconds = 0
                        if speed_mbps > 0 and total_size > 0:
                            remaining_bits = (total_size - downloaded) * 8
                            eta_seconds = int(remaining_bits / (speed_mbps * 1_000_000))

                        self.active_downloads_status[download_id] = {
                            "filename": local_filename,
                            "image": image,
                            "progress": percent,
                            "speed": speed_mbps,
                            "eta": eta_seconds,
                            "status": "downloading"
                        }

                        if progress_callback and total_size > 0:
                            progress_callback(download_id, local_filename, percent, speed_mbps, eta_seconds)
                        
                        if self.speed_limit_mbps and self.speed_limit_mbps > 0:
                            bytes_per_sec = int((self.speed_limit_mbps * 1_000_000) / 8)
                            expected_time = (downloaded / bytes_per_sec) if bytes_per_sec > 0 else 0
                            if expected_time > total_elapsed:
                                time.sleep(expected_time - total_elapsed)
                                
            if progress_callback:
                progress_callback(download_id, local_filename, 1.0, 0, 0)

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
                    print(f"Archive extraction failed: {ex}")

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
            for mapping in [
                self.active_downloads, self.active_downloads_status,
                self.pause_events, self.paused_downloads,
                self.total_paused_durations, self.speed_adjustment_baselines
            ]:
                mapping.pop(download_id, None)

    def stop_download(self, download_id: str):
        """Halt and terminate an active download thread."""
        if download_id in self.active_downloads:
            self.active_downloads[download_id] = False
            if download_id in self.pause_events:
                self.pause_events[download_id].set()

    def update_speed_limit(self, new_limit: float):
        """Dynamically update bandwidth caps and trigger baseline adjustments for threads."""
        self.speed_limit_mbps = new_limit
        for download_id in self.active_downloads.keys():
            self.speed_adjustment_baselines[download_id] = True

    def get_active_downloads_status(self):
        """Return active download metrics registry."""
        return self.active_downloads_status


downloader_engine = FileDownloader()