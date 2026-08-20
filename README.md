# 📥 FitGirl Repacks Real-Debrid Downloader

A sleek, feature-rich desktop client designed to browse FitGirl repacks and interface directly with Real-Debrid for lightning-fast, secure cloud downloads.

---

## 🤖 Development & AI Disclosure

* **AI-Assisted Project:** This project was developed with the assistance of artificial intelligence tools (such as large language models) to help structure, write, optimize, and debug both the frontend TypeScript/React interface and the backend Python/Tauri architecture.

---

## ⚠️ Important Requirement

* **Real-Debrid Account Required:** This application functions exclusively as a client interface for **Real-Debrid**. You must have an active Real-Debrid subscription and a valid API token for this tool to function.

---

## 🚀 Getting Started (Portable Setup)

Because this tool runs locally and generates its configuration files on the fly, please follow these simple steps to run it properly:

1. Create a brand-new, empty folder anywhere on your computer (e.g., `DebridDownloader`).
2. Download the release ZIP archive containing both the application executable (`fitgirl-downloader.exe`) and the backend (`server.exe`) sidecar file.
3. Extract both files into your newly created folder.
4. Double-click `fitgirl-downloader.exe` to launch it. 
   *(Note: On first launch, the app will automatically generate its local configuration and cache files right inside this folder).*

---

## 📂 Local Runtime Files & Caches

When running the application, you will notice several local data files created automatically in your folder. Here is what each file is used for:

* **`server.exe`**: The local Python/FastAPI backend sidecar responsible for parsing web data, interacting with Real-Debrid, and managing downloads.
* **`Downloads/` folder**: The dedicated directory where your completed downloads and automatically extracted files are stored. *(Note: This folder is automatically created only when you start downloading a game).*
* **`download_history.json`**: A local ledger tracking all your completed download tasks and history logs.
* **`pages_cache.json`**: Caches general paginated repack directory structures to load listings quickly.
* **`popular_cache.json`**: Stores weekly trending repack data to make popular browsing instant.
* **`repacks_cache.json`**: Maintains a local index of recent repack releases.
* **`upcoming_cache.json`**: Saves schedule tracking data for upcoming repacks.

---

## 🔑 Real-Debrid API Token Setup

1. Log into your account at [Real-Debrid](https://real-debrid.com).
2. Go to your API token management page at **[real-debrid.com/apitoken](https://real-debrid.com/apitoken)** and copy your token.
3. Open the app, navigate to the **Settings** menu via the sidebar, paste your token into the **Real-Debrid API Token** field, and click **Save Key**.
4. Once authenticated, the status indicator will glow **Green** (indicating active Real-Debrid Premium status), and your key will automatically be saved locally.

---

## 🧭 Navigation Sidebar Overview

The application features a clean sidebar layout to easily switch between views:

* **Recent Repacks:** View the latest releases and updates. This view supports **multiple ways to navigate**: you can seamlessly scroll through the dynamic list, use the side arrow buttons (`->`) on the edges to flip through items quickly, or use the built-in **Previous/Next Page** controls at the bottom to jump through pages across the library.
* **Most Popular of the week:** Easily check out what's trending.
* **Upcoming Repacks:** Stay ahead of the schedule with a dedicated tab for upcoming releases.
* **Active Download Que:** Queue up and manage active downloads running sequentially.
* **Download History:** View a comprehensive log of all completed downloads with quick-access file options.
* **Settings:** Access all core application configurations and preferences.

---

## ⚙️ Settings Menu Overview

All of your preferences are neatly organized inside the **Settings** view:

* **Appearance & Themes:** Choose a color palette for your launcher interface on the fly, supporting options like **Pure Obsidian**, **Midnight Steam**, **Dark Emerald**, and **Crimson Void**.
* **Minimize to System Tray:** Toggle this option on or off. When enabled, closing the application window minimizes it to the system tray so your active background downloads can keep running seamlessly. When disabled, closing the window completely exits the app and terminates background server processes.
* **Real-Debrid API Token:** Paste your token directly into the input field and click **Save Key** to link your account. Required for resolving torrent magnets and starting cloud downloads.
* **Bandwidth Speed Limit:** Set a maximum transfer rate cap in Mbps for active queue tasks and click **Apply Limit**.
* **Clear Stored Data & API Key:** Instantly wipe your saved Real-Debrid token and local cache before removing the application.

---

## ✨ Key Features

* **Live Status Indicators:** 
  * 🟢 **Real-Debrid:** Glows green when your account is successfully authenticated.
  * 🟢 **FitGirl Site:** Glows green to indicate the live website connection is online.
* **Visual Metadata & Artwork:** Game cards feature official high-resolution cover artwork and clean release names.
* **Advanced Download Manager & Tracking:**
  * **Main Page Progress Bar:** Monitor your active downloads instantly via a live progress bar and speed indicator displayed right on the main interface while downloading.
  * **Active Queue & Granular Controls:** Dedicated management panel to view queue items with options to pause, resume, cancel, and remove tasks.
  * **Auto-Extraction:** Automatically unzips and extracts downloaded archive contents directly into their own dedicated folder upon completion.
* **Immersive Game Details View:** Click on any game card to open a dedicated page featuring scraped official descriptions, repack features, and an interactive screenshot gallery.
* **In-App Toast Notifications:** Real-time visual notification pop-ups appear in the corner of your screen to alert you instantly to system actions (such as saving API keys, updating limits, toggling settings, and queue updates).

---

## 💡 How It Works

* **Client-Side Interface:** This application acts strictly as an RSS/link parser and download manager interface. It grabs magnet links and securely passes them to your authenticated Real-Debrid account.
* **Account Syncing:** When you start a download, it automatically syncs with your Real-Debrid account, allowing you to view progress or manage transfers directly from the official website as well.
* **Zero P2P Exposure:** No copyrighted files, torrents, or media are ever hosted, stored, cached, or seeded by this application. All downloads are direct high-speed HTTP streams handled entirely by Real-Debrid's servers, keeping your local network completely detached from the P2P swarm.

---

## 🏗️ Architecture & Technology Stack

This application is built on a modern high-performance hybrid architecture:

* **Frontend & Desktop Shell (Tauri & Rust):** Built using Tauri and Rust to provide a lightning-fast, native desktop application wrapper. Handles window events, dynamic system tray integration, and bulletproof background process tree cleanup (`taskkill`).
* **Backend Core (Python & FastAPI):** Powered by a local background sidecar (`server.exe`) running entirely on your machine (`localhost`). 
* **Local Security & Privacy:** Because the server operates strictly as a local instance on your computer, **no outbound external telemetry or unauthorized connections are made**. It communicates exclusively with your authenticated Real-Debrid API and public web data to parse links, ensuring your local network remains completely secure.

---

## 📸 App Previews

* **Main Interface & Recent Releases** (`Main Interface & Recent Releases.png`)
* **Most Popular Repacks of the Week** (`Most Popular Repacks of the Week.png`)
* **Upcoming Repacks Schedule** (`Upcoming Repacks Schedule.png`)
* **Integrated Search Functionality** (`Integrated Search Functionality.png`)
* **Selective Downloading & File Management** (`Selective Downloading & File Management.png`)
* **Active Downloads & Speed Limiter** (`Active Downloads & Speed Limiter.png`)
* **Downloads & File Extraction** (`Downloads Extracted .png`)
* **Live Repack Features & File Selection** (`Details.png` & `Details 2.png`)
* **Real-Debrid Dashboard Integration** (`Real-Debrid Tracking .png`)
* **Clean & Portable Local File Structure** (`Files created after starting exe.png`)

---

## 💖 Support the Original Creator

* **Support FitGirl:** This tool interacts with data provided by FitGirl Repacks. If you appreciate her work, please consider supporting her directly by visiting the official [FitGirl Repacks Donations Page](https://fitgirl-repacks.site/donations/).

---

*Disclaimer: This project is an independent, open-source client application designed solely to interface with Real-Debrid and public web data. The author does not host, store, cache, upload, or distribute any ROMs, media, torrents, or copyrighted content. All data processing and direct downloads are handled entirely via third-party services and the user's personal Real-Debrid account. This tool is provided "as is" without warranty of any kind.*
