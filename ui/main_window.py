import customtkinter as ctk
import threading
from PIL import Image
import requests
import io
import os
import sys
import json
from bs4 import BeautifulSoup
from core.scraper import search_fitgirl_api, get_recent_fitgirl_posts, get_popular_repacks, get_upcoming_repacks, check_site_status
from core.debrid_api import add_magnet_get_info, confirm_files_selection, get_user_account_info
from core.downloader import downloader_engine, load_history, HAS_NOTIFICATIONS

if HAS_NOTIFICATIONS:
    from plyer import notification

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("FitGirl Repacks Real-Debrid Downloader")
        self.geometry("1200x750")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.current_view = "recent"
        self.active_downloads = {}

        # --- Left Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Downloader", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 5))

        # Real-Debrid Account Status Widget Badge
        self.account_badge = ctk.CTkLabel(self.sidebar_frame, text="RD Status: Checking...", font=("Arial", 10), text_color="orange")
        self.account_badge.grid(row=1, column=0, padx=20, pady=(0, 2))

        # FitGirl Site Status Widget Badge
        self.fitgirl_badge = ctk.CTkLabel(self.sidebar_frame, text="FitGirl: Checking...", font=("Arial", 10), text_color="orange")
        self.fitgirl_badge.grid(row=2, column=0, padx=20, pady=(0, 10))

        # Custom API Key Entry Section
        self.api_key_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Enter RD API Key...", width=180, show="*")
        self.api_key_entry.grid(row=3, column=0, padx=20, pady=(0, 5))
        
        # Pre-load saved API key if available
        saved_key = self.load_saved_api_key()
        if saved_key:
            self.api_key_entry.insert(0, saved_key)
        
        self.api_save_btn = ctk.CTkButton(self.sidebar_frame, text="Update API Key", width=180, height=28, command=self.update_api_key)
        self.api_save_btn.grid(row=4, column=0, padx=20, pady=(0, 15))

        self.nav_home = ctk.CTkButton(
            self.sidebar_frame, text="Home / Recent", 
            command=self.show_startup_recent,
            fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE")
        )
        self.nav_home.grid(row=5, column=0, padx=20, pady=8)

        self.nav_games = ctk.CTkButton(
            self.sidebar_frame, text="Most Popular of the Week", 
            command=self.show_game_repacks,
            fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE")
        )
        self.nav_games.grid(row=6, column=0, padx=20, pady=8)

        self.nav_upcoming = ctk.CTkButton(
            self.sidebar_frame, text="Upcoming Repacks", 
            command=self.show_upcoming_view,
            fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE")
        )
        self.nav_upcoming.grid(row=7, column=0, padx=20, pady=8)

        self.nav_downloads = ctk.CTkButton(
            self.sidebar_frame, text="Downloads", 
            command=self.show_downloads_view,
            fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE")
        )
        self.nav_downloads.grid(row=8, column=0, padx=20, pady=8)

        self.nav_history = ctk.CTkButton(
            self.sidebar_frame, text="Library / History", 
            command=self.show_history_view,
            fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE")
        )
        self.nav_history.grid(row=9, column=0, padx=20, pady=8)

        # Theme Selector Dropdown in Sidebar
        self.theme_menu = ctk.CTkOptionMenu(
            self.sidebar_frame, values=["blue", "green", "dark-blue"],
            command=self.change_theme_color, width=180
        )
        self.theme_menu.grid(row=10, column=0, padx=20, pady=(10, 20), sticky="s")
        self.theme_menu.set("blue")

        # --- Main Content Area ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search for a game...", width=280, height=40)
        self.search_entry.pack(side="left", padx=(0, 10))
        
        self.search_button = ctk.CTkButton(self.search_frame, text="Search", command=self.perform_search, height=40)
        self.search_button.pack(side="left", padx=(0, 10))

        self.refresh_button = ctk.CTkButton(self.search_frame, text="🔄 Refresh", command=self.manual_refresh, height=40, width=85, fg_color="gray30", hover_color="gray40")
        self.refresh_button.pack(side="left", padx=(0, 15))

        self.speed_label = ctk.CTkLabel(self.search_frame, text="Limit (Mbps):", font=("Arial", 11, "bold"))
        self.speed_label.pack(side="left", padx=(0, 5))

        self.speed_entry = ctk.CTkEntry(self.search_frame, width=70, height=40)
        self.speed_entry.pack(side="left", padx=(0, 5))
        self.speed_entry.insert(0, "250")

        self.results_scroll = ctk.CTkScrollableFrame(self.main_frame)
        self.results_scroll.grid(row=1, column=0, sticky="nsew")
        self.results_scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.after(50, self.show_startup_recent)
        self.after(100, self.check_rd_account)
        self.after(150, self.check_site_status)
        self._poll_downloads_view()

    def load_saved_api_key(self):
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    data = json.load(f)
                    return data.get("rd_api_key", "")
        except Exception:
            pass
        return ""

    def save_api_key_to_disk(self, key):
        try:
            with open("config.json", "w") as f:
                json.dump({"rd_api_key": key}, f)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def get_current_api_key(self):
        key = self.api_key_entry.get().strip()
        if key:
            return key
        saved_key = self.load_saved_api_key()
        if saved_key:
            return saved_key
        return None

    def update_api_key(self):
        key = self.api_key_entry.get().strip()
        if key:
            self.save_api_key_to_disk(key)
        self.check_rd_account()

    def check_rd_account(self):
        threading.Thread(target=self._fetch_account_thread, daemon=True).start()

    def _fetch_account_thread(self):
        account_data = get_user_account_info(self.get_current_api_key())
        if account_data and 'type' in account_data:
            acc_type = account_data.get('type', 'Unknown')
            text = f"RD: {acc_type.capitalize()}"
            self.after(0, lambda: self.account_badge.configure(text=text, text_color="green"))
        else:
            self.after(0, lambda: self.account_badge.configure(text="RD: Invalid Key", text_color="red"))

    def check_site_status(self):
        threading.Thread(target=self._fetch_site_status_thread, daemon=True).start()

    def _fetch_site_status_thread(self):
        is_up = check_site_status()
        if is_up:
            self.after(0, lambda: self.fitgirl_badge.configure(text="FitGirl: Online", text_color="green"))
        else:
            self.after(0, lambda: self.fitgirl_badge.configure(text="FitGirl: Offline", text_color="red"))

    def change_theme_color(self, new_theme):
        ctk.set_default_color_theme(new_theme)
        if self.current_view == "recent":
            self.show_startup_recent()
        elif self.current_view == "popular":
            self.show_game_repacks()
        elif self.current_view == "upcoming":
            self.show_upcoming_view()
        elif self.current_view == "downloads":
            self.show_downloads_view()
        elif self.current_view == "history":
            self.show_history_view()
            
    def show_startup_recent(self):
        self.current_view = "recent"
        for widget in self.results_scroll.winfo_children(): 
            widget.destroy()
        self.results_scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)
        ctk.CTkLabel(self.results_scroll, text="Loading latest repacks...").grid(row=0, column=0, columnspan=4, pady=20)
        threading.Thread(target=self._load_recent_thread, args=(False,), daemon=True).start()

    def _load_recent_thread(self, force_refresh):
        results = get_recent_fitgirl_posts(force_refresh=force_refresh)
        self.after(0, lambda: self._update_grid_safely(results))

    def show_game_repacks(self):
        self.current_view = "popular"
        for widget in self.results_scroll.winfo_children(): 
            widget.destroy()
        self.results_scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)
        ctk.CTkLabel(self.results_scroll, text="Loading Most Popular Repacks of the Week...").grid(row=0, column=0, columnspan=4, pady=20)
        threading.Thread(target=self._load_popular_thread, args=(False,), daemon=True).start()

    def _load_popular_thread(self, force_refresh):
        results = get_popular_repacks(force_refresh=force_refresh)
        self.after(0, lambda: self._update_grid_safely(results))

    def show_upcoming_view(self):
        self.current_view = "upcoming"
        for widget in self.results_scroll.winfo_children(): 
            widget.destroy()
        self.results_scroll.grid_columnconfigure((0, 1, 2, 3), weight=0)
        self.results_scroll.grid_columnconfigure(0, weight=1)
        self.results_scroll.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.results_scroll, text="Upcoming Repacks Schedule", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        ctk.CTkLabel(self.results_scroll, text="Fetching upcoming queue from FitGirl site...", text_color="gray").grid(row=1, column=0, columnspan=2, pady=20)
        
        threading.Thread(target=self._load_upcoming_thread, daemon=True).start()

    def _load_upcoming_thread(self):
        items = get_upcoming_repacks()
        self.after(0, lambda: self._update_upcoming_grid(items))

    def _update_upcoming_grid(self, items):
        for widget in self.results_scroll.winfo_children(): 
            widget.destroy()
            
        if not items:
            ctk.CTkLabel(self.results_scroll, text="Could not load upcoming repacks schedule.", text_color="gray").grid(row=1, column=0, columnspan=2, pady=20)
            return

        ctk.CTkLabel(self.results_scroll, text="Upcoming Repacks Schedule", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(10, 10), sticky="w")
        
        self.results_scroll.grid_columnconfigure(0, weight=1)
        self.results_scroll.grid_columnconfigure(1, weight=1)
        
        for idx, item in enumerate(items):
            row_idx = (idx // 2) + 1
            col_idx = idx % 2

            card = ctk.CTkFrame(self.results_scroll, corner_radius=4)
            card.grid(row=row_idx, column=col_idx, padx=4, pady=2, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)

            lbl = ctk.CTkLabel(card, text=item['title'], font=("Arial", 11), anchor="w", justify="left", wraplength=380)
            lbl.grid(row=0, column=0, padx=8, pady=4, sticky="w")

    def manual_refresh(self):
        for widget in self.results_scroll.winfo_children(): 
            widget.destroy()
        if self.current_view == "recent":
            ctk.CTkLabel(self.results_scroll, text="Force-refreshing latest repacks...").grid(row=0, column=0, columnspan=4, pady=20)
            threading.Thread(target=self._load_recent_thread, args=(True,), daemon=True).start()
        elif self.current_view == "popular":
            ctk.CTkLabel(self.results_scroll, text="Scraping fresh weekly popular repacks...").grid(row=0, column=0, columnspan=4, pady=20)
            threading.Thread(target=self._load_popular_thread, args=(True,), daemon=True).start()
        elif self.current_view == "upcoming":
            self.show_upcoming_view()

    def _update_grid_safely(self, results):
        for widget in self.results_scroll.winfo_children(): 
            widget.destroy()
        if not results:
            ctk.CTkLabel(self.results_scroll, text="No games found or failed to load.").grid(row=0, column=0, columnspan=4, pady=20)
            return
        self.populate_grid(results)

    def show_downloads_view(self):
        self.current_view = "downloads"
        for widget in self.results_scroll.winfo_children(): 
            widget.destroy()
        self.results_scroll.grid_columnconfigure(0, weight=1)
        for i in range(1, 4):
            self.results_scroll.grid_columnconfigure(i, weight=0)

        ctk.CTkLabel(self.results_scroll, text="Active Downloads Manager & Queue", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=(10, 20), sticky="w")
        
        if not self.active_downloads:
            ctk.CTkLabel(self.results_scroll, text="No active downloads right now.", text_color="gray").grid(row=1, column=0, pady=20)
        else:
            row_idx = 1
            for download_id, data in self.active_downloads.items():
                self._build_download_card(download_id, data, row_idx)
                row_idx += 1

    def show_history_view(self):
        self.current_view = "history"
        for widget in self.results_scroll.winfo_children(): 
            widget.destroy()
        self.results_scroll.grid_columnconfigure(0, weight=1)
        for i in range(1, 4):
            self.results_scroll.grid_columnconfigure(i, weight=0)

        ctk.CTkLabel(self.results_scroll, text="Download Library & History", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=(10, 20), sticky="w")
        
        history_items = load_history()
        if not history_items:
            ctk.CTkLabel(self.results_scroll, text="No completed download history found yet.", text_color="gray").grid(row=1, column=0, pady=20)
            return

        row_idx = 1
        for item in history_items:
            card = ctk.CTkFrame(self.results_scroll, corner_radius=10)
            card.grid(row=row_idx, column=0, padx=5, pady=8, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            lbl = ctk.CTkLabel(card, text=item['filename'], font=("Arial", 12, "bold"))
            lbl.grid(row=0, column=0, padx=15, pady=(10, 2), sticky="w")

            date_lbl = ctk.CTkLabel(card, text=f"Completed: {item['date']}", font=("Arial", 11), text_color="gray")
            date_lbl.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

            folder_btn = ctk.CTkButton(card, text="📁 Open Folder", width=120, 
                                       command=lambda path=item['path']: self.open_file_folder(path))
            folder_btn.grid(row=0, column=1, rowspan=2, padx=15, pady=10, sticky="e")

            row_idx += 1

    def open_file_folder(self, file_path):
        folder = file_path if os.path.isdir(file_path) else os.path.dirname(os.path.abspath(file_path))
        if os.path.exists(folder):
            os.startfile(folder)

    def _build_download_card(self, download_id, data, row):
        card = ctk.CTkFrame(self.results_scroll, corner_radius=10)
        card.grid(row=row, column=0, padx=5, pady=8, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(card, text=data.get('filename', 'Unknown file'), font=("Arial", 12, "bold"))
        lbl.grid(row=0, column=0, padx=15, pady=(10, 2), sticky="w")

        status_text = f"Speed: {round(data.get('speed', 0), 2)} Mbps — {int(data.get('progress', 0) * 100)}%"
        status_lbl = ctk.CTkLabel(card, text=status_text, font=("Arial", 11), text_color="gray")
        status_lbl.grid(row=1, column=0, padx=15, pady=(0, 5), sticky="w")

        pbar = ctk.CTkProgressBar(card, width=480)
        pbar.grid(row=2, column=0, padx=15, pady=(0, 12), sticky="w")
        pbar.set(data.get('progress', 0))

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=2, column=1, padx=10, pady=(0, 12), sticky="e")

        stop_btn = ctk.CTkButton(btn_frame, text="Stop", width=75, fg_color="#b30000", hover_color="#800000",
                                 command=lambda did=download_id: self.stop_download_action(did))
        stop_btn.pack(side="left", padx=4)

        delete_btn = ctk.CTkButton(btn_frame, text="🗑 Delete", width=85, fg_color="gray40", hover_color="gray50",
                                   command=lambda did=download_id: self.delete_download_action(did))
        delete_btn.pack(side="left", padx=4)

        data['widgets'] = {'status': status_lbl, 'pbar': pbar, 'stop_btn': stop_btn, 'delete_btn': delete_btn}

    def update_download_progress(self, download_id, filename, progress, speed):
        if download_id in self.active_downloads:
            self.active_downloads[download_id].update({
                'filename': filename,
                'progress': progress,
                'speed': speed
            })

    def stop_download_action(self, download_id):
        downloader_engine.stop_download(download_id)
        if download_id in self.active_downloads:
            self.active_downloads[download_id]['progress'] = 0
            self.active_downloads[download_id]['speed'] = 0
            if 'widgets' in self.active_downloads[download_id]:
                w = self.active_downloads[download_id]['widgets']
                w['status'].configure(text="Stopped by user", text_color="orange")
                w['stop_btn'].configure(state="disabled")

    def delete_download_action(self, download_id):
        downloader_engine.stop_download(download_id)
        if download_id in self.active_downloads:
            filename = self.active_downloads[download_id].get('filename')
            if filename:
                file_path = os.path.join("Downloads", filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
            del self.active_downloads[download_id]
            self.show_downloads_view()

    def _poll_downloads_view(self):
        if self.current_view == "downloads" and self.active_downloads:
            for download_id, data in self.active_downloads.items():
                if 'widgets' in data:
                    widgets = data['widgets']
                    prog = data.get('progress', 0)
                    spd = data.get('speed', 0)
                    widgets['pbar'].set(prog)
                    status_text = f"Speed: {round(spd, 2)} Mbps — {int(prog * 100)}%"
                    if prog >= 1.0:
                        widgets['status'].configure(text="Download Complete & Extracted!", text_color="green")
                        widgets['stop_btn'].configure(state="disabled")
                    elif widgets['status'].cget("text") != "Stopped by user":
                        widgets['status'].configure(text=status_text)
                        
        self.after(500, self._poll_downloads_view)

    def notify_queue_complete(self):
        if HAS_NOTIFICATIONS:
            try:
                notification.notify(
                    title="Queue Complete!",
                    message="All files have finished downloading and extracting successfully.",
                    timeout=5
                )
            except Exception:
                pass

    def perform_search(self):
        query = self.search_entry.get()
        if not query: 
            return
        self.current_view = "search"
        for widget in self.results_scroll.winfo_children(): 
            widget.destroy()
        self.results_scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)
        ctk.CTkLabel(self.results_scroll, text="Searching FitGirl...").grid(row=0, column=0, columnspan=4, pady=20)
        threading.Thread(target=self._search_thread, args=(query,), daemon=True).start()

    def _search_thread(self, query):
        results = search_fitgirl_api(query)
        self.after(0, lambda: self._update_grid_safely(results))

    def populate_grid(self, results):
        row_idx = 0
        col_idx = 0
        for game in results:
            self._build_game_card(game, row_idx, col_idx)
            col_idx += 1
            if col_idx > 3:
                col_idx = 0
                row_idx += 1

    def _build_game_card(self, game, row, col):
        card = ctk.CTkFrame(self.results_scroll, corner_radius=10)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        display_title = game['title'][:30] + "..." if len(game['title']) > 30 else game['title']
        title_lbl = ctk.CTkLabel(card, text=display_title, font=("Arial", 12, "bold"), wraplength=150)
        title_lbl.pack(pady=(10, 5), padx=10)

        img_lbl = ctk.CTkLabel(card, text="Loading image...", width=150, height=200)
        img_lbl.pack(pady=5)

        if game.get('image'):
            threading.Thread(target=self._load_card_image, args=(game['image'], img_lbl), daemon=True).start()

        # Passes both magnet link and page URL for live scraping
        game_url = game.get('link', game.get('url', ''))
        btn = ctk.CTkButton(card, text="Download", command=lambda m=game['magnet'], u=game_url: self.start_download(m, u))
        btn.pack(pady=(10, 10), padx=10)

    def _load_card_image(self, img_url, img_lbl):
        try:
            response = requests.get(img_url, stream=True, timeout=5)
            if response.status_code == 200:
                img_data = Image.open(io.BytesIO(response.content))
                ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(150, 200))
                self.after(0, lambda: img_lbl.configure(image=ctk_img, text=""))
        except Exception:
            self.after(0, lambda: img_lbl.configure(text="[No Image]"))

    def start_download(self, magnet_link, game_url=None):
        loading_popup = ctk.CTkToplevel(self)
        loading_popup.geometry("300x150")
        loading_popup.title("Fetching Files...")
        loading_popup.grab_set()
        
        ctk.CTkLabel(loading_popup, text="Contacting Real-Debrid...\nAnalyzing torrent contents.", font=("Arial", 12)).pack(expand=True, padx=20, pady=20)
        
        threading.Thread(target=self._fetch_torrent_info_thread, args=(magnet_link, game_url, loading_popup), daemon=True).start()

    def _fetch_torrent_info_thread(self, magnet_link, game_url, loading_popup):
        torrent_info = add_magnet_get_info(magnet_link, self.get_current_api_key())
        loading_popup.destroy()
        
        if not torrent_info:
            print("Failed to fetch torrent information.")
            return
            
        self.after(0, lambda: self.open_file_selection_dialog(torrent_info, game_url))

    def open_file_selection_dialog(self, torrent_info, game_url=None):
        dialog = ctk.CTkToplevel(self)
        dialog.geometry("700x580")
        dialog.title(f"Download & Repack Details — {torrent_info['filename']}")
        dialog.grab_set()

        # Tabbed interface for file selection + live details
        tabview = ctk.CTkTabview(dialog)
        tabview.pack(padx=15, pady=(5, 15), fill="both", expand=True)

        tab_files = tabview.add("📁 Select Files")
        tab_details = tabview.add("📋 Repack Features & Details")

        # --- Tab 1: File Selection ---
        ctk.CTkLabel(tab_files, text=torrent_info['filename'], font=("Arial", 14, "bold")).pack(pady=(10, 2))
        ctk.CTkLabel(tab_files, text="Uncheck any optional bins, language packs, or bonuses you don't want:", text_color="gray").pack(pady=(0, 10))

        scroll_frame = ctk.CTkScrollableFrame(tab_files, width=620, height=320)
        scroll_frame.pack(padx=10, pady=5, fill="both", expand=True)

        checkbox_vars = []
        for file_item in torrent_info['files']:
            var = ctk.BooleanVar(value=True)
            path = file_item.get('path', 'Unknown file')
            size_mb = round(file_item.get('bytes', 0) / (1024 * 1024), 2)
            file_id = file_item.get('id')
            
            label_text = f"{path} ({size_mb} MB)"
            chk = ctk.CTkCheckBox(scroll_frame, text=label_text, variable=var)
            chk.pack(anchor="w", pady=4, padx=5)
            
            checkbox_vars.append((file_id, var))

        def confirm_selection():
            selected_ids = [fid for fid, var in checkbox_vars if var.get()]
            dialog.destroy()
            
            try:
                limit_val = float(self.speed_entry.get())
            except ValueError:
                limit_val = None

            threading.Thread(target=self._finalize_download_thread, args=(torrent_info['id'], selected_ids, limit_val), daemon=True).start()

        confirm_btn = ctk.CTkButton(tab_files, text="Start Torrent Download", command=confirm_selection, fg_color="green", hover_color="darkgreen", height=40)
        confirm_btn.pack(pady=12)

        # --- Tab 2: Live Scraped Features & Info ---
        details_scroll = ctk.CTkScrollableFrame(tab_details)
        details_scroll.pack(padx=10, pady=10, fill="both", expand=True)

        loading_label = ctk.CTkLabel(
            details_scroll, 
            text="Fetching live repack features and game details from site...", 
            font=("Arial", 12)
        )
        loading_label.pack(pady=20)

        if game_url:
            threading.Thread(target=self._fetch_live_details_thread, args=(game_url, details_scroll, loading_label), daemon=True).start()
        else:
            loading_label.configure(text="No direct webpage URL available to scrape details for this item.")

    def _fetch_live_details_thread(self, game_url, scroll_frame, loading_label):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(game_url, headers=headers, timeout=10)
            
            parsed_items = []
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                content_div = soup.find('div', class_='entry-content')
                
                if content_div:
                    skip_next_ul = False
                    
                    for child in content_div.children:
                        if child.name is None:
                            continue
                            
                        text = child.get_text().strip()
                        
                        # --- The Smart Filter ---
                        if child.name in ['h3', 'h4', 'p', 'strong'] and 'Download Mirrors' in text:
                            skip_next_ul = True
                            continue 
                            
                        if skip_next_ul and child.name == 'ul':
                            skip_next_ul = False
                            continue
                            
                        for img in child.find_all('img'):
                            img_url = img.get('src')
                            if img_url:
                                parsed_items.append({'type': 'image', 'url': img_url})
                                
                        if text:
                            parsed_items.append({'type': 'text', 'content': text})
                            
                    if not parsed_items:
                        parsed_items.append({'type': 'text', 'content': "No detailed repack features found on the page."})
                else:
                    parsed_items.append({'type': 'text', 'content': "Could not locate main entry-content block on the page."})
            else:
                parsed_items.append({'type': 'text', 'content': f"HTTP Error {response.status_code} while fetching page details."})
                
            self.after(0, lambda: self._render_live_details(parsed_items, scroll_frame, loading_label))
            
        except Exception as e:
            self.after(0, lambda: loading_label.configure(text=f"Error fetching live details: {e}"))

    def _render_live_details(self, parsed_items, scroll_frame, loading_label):
        loading_label.destroy()
        
        for item in parsed_items:
            if item['type'] == 'text':
                lbl = ctk.CTkLabel(scroll_frame, text=item['content'], justify="left", wraplength=600, font=("Arial", 12))
                lbl.pack(anchor="nw", padx=10, pady=(0, 15))
            elif item['type'] == 'image':
                img_lbl = ctk.CTkLabel(scroll_frame, text="Loading image...")
                img_lbl.pack(anchor="nw", padx=10, pady=(0, 15))
                threading.Thread(target=self._load_detail_image, args=(item['url'], img_lbl), daemon=True).start()

    def _load_detail_image(self, img_url, img_lbl):
        try:
            response = requests.get(img_url, stream=True, timeout=5)
            if response.status_code == 200:
                img_data = Image.open(io.BytesIO(response.content))
                
                width, height = img_data.size
                if width > 600:
                    ratio = 600 / width
                    new_size = (600, int(height * ratio))
                else:
                    new_size = (width, height)
                    
                ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=new_size)
                self.after(0, lambda: img_lbl.configure(image=ctk_img, text=""))
        except Exception:
            self.after(0, lambda: img_lbl.configure(text="[Image Failed to Load]"))

    def _finalize_download_thread(self, torrent_id, selected_ids, speed_limit):
        print(f"Sending selected files to Real-Debrid...")
        download_links = confirm_files_selection(torrent_id, selected_ids, self.get_current_api_key())
        if not download_links: 
            print("Failed to get download links.")
            return
            
        print(f"Queuing {len(download_links)} files...")
        for link in download_links:
            download_id = str(abs(hash(link)))
            self.active_downloads[download_id] = {
                'filename': link.split('/')[-1].split('?')[0], 
                'progress': 0.0, 
                'speed': 0.0
            }

        downloader_engine.add_to_queue(
            download_tasks=download_links,
            speed_limit=speed_limit,
            progress_callback=self.update_download_progress,
            queue_complete_callback=self.notify_queue_complete
        )