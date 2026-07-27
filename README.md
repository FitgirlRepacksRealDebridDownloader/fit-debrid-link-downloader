# 📥 FitGirl Repacks Real-Debrid Downloader

A sleek, feature-rich desktop client designed to interface directly with Real-Debrid and browse/download content seamlessly.

---

## ⚠️ Important Requirement
* **Real-Debrid Account Required:** This application functions exclusively as a client interface for **Real-Debrid**. You must have an active Real-Debrid subscription and a valid API token for this tool to function.

---

## 🚀 Getting Started (Installation)

Because this tool generates local configuration and tracking files at runtime, please follow these steps to run it properly:

1. Create a brand-new, empty folder anywhere on your computer (e.g., `DebridDownloader`).
2. Download the latest compiled `.exe` from the **Releases** page.
3. Move the `.exe` file inside your newly created folder.
4. Double-click the `.exe` to launch it. 
   *(Note: On first launch, the app will automatically generate its local configuration files inside this folder).*

---

## 🔑 Real-Debrid API Token Setup

1. Log into your account at [Real-Debrid](https://real-debrid.com).
2. Go to your API token management page at **[real-debrid.com/apitoken](https://real-debrid.com/apitoken)** and copy your token.
3. Paste your token directly into the input field inside the application's sidebar and click **Update API Key**.
4. Once authenticated, the status indicator will glow **Green** (indicating active Real-Debrid Premium status), and your key will automatically be saved locally to a `config.json` file so you don't have to re-enter it.

---

## ✨ Key Features

* **Live Status Indicators:** 
  * 🟢 **RD:** Glows green when your Real-Debrid account is successfully authenticated.
  * 🟢 **FitGirl:** Glows green to let you know the website connection status is online.
* **Curated Browsing Tabs:**
  * **Home / Recent:** View the latest releases and updates right at your fingertips.
  * **Most Popular of the Week:** Easily check out what's trending.
  * **Upcoming Repacks:** Stay ahead of the curve with a dedicated tab for upcoming releases.
* **Visual Metadata & Badges:** Game cards feature official artwork and clear tags (such as **HV** badges to instantly let you know if a release is a Hypervisor bypass).
* **Advanced Download Manager:**
  * **Queue System:** Queue up multiple downloads to run sequentially once active downloads finish.
  * **Control Panel:** Easily start, stop, or delete active downloads.
  * **Auto-Extraction:** Automatically unzips and extracts downloaded archive contents directly into their own dedicated folder inside your downloads directory upon completion.
* **Speed Limiter:** Fine-tune your bandwidth using the built-in speed adjustment settings (Mbps).
* **Built-in Search:** Quickly look up specific games using the integrated search tool.

---

## 💡 How It Works
* **Client-Side Only:** This application acts strictly as an RSS/link parser and download manager interface. 
* **Zero Hosting:** No copyrighted files, torrents, or media are ever hosted, stored, cached, or seeded by this application. All direct downloads are handled securely through your authenticated Real-Debrid account.