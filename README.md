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
* **Advanced Download Manager & History:**
  * **Queue System:** Queue up multiple downloads to run sequentially once active downloads finish.
  * **Granular Control Panel:** Full management controls for active tasks with dedicated **Pause**, **Resume**, **Stop**, and **🗑 Delete** buttons.
  * **Auto-Extraction:** Automatically unzips and extracts downloaded archive contents directly into their own dedicated folder inside your downloads directory upon completion.
  * **Library & History Tracker:** View a comprehensive log of all completed downloads with quick-access **📁 Open Folder** buttons.
* **Speed Limiter:** Fine-tune your bandwidth using the built-in speed adjustment settings (Mbps).
* **Built-in Search:** Quickly look up specific games using the integrated search tool.
* * **Live Repack Details & Features Window:** Click the **📋 Features & Details** button on any game card to open a dedicated pop-up window displaying live scraped official game descriptions, repack features, and screenshots. Note: Certain newer releases with unique structural formats may display a notice stating that detailed text descriptions are unavailable due to how they are set up, directing you to check the website directly.
* **Dynamic Theme Customization:** Switch up your app's look on the fly using the built-in theme selector in the sidebar, supporting vibrant accents including **Blue, Dark-Blue, Green, Purple, Orange, Red, and Teal**.

---

## 💡 How It Works
* **Client-Side Only:** This application acts strictly as an RSS/link parser and download manager interface. It simply parses the website to grab magnet links and securely passes them directly to your authenticated Real-Debrid account for processing.
* **Account Syncing:** When you start a download in the app, it automatically syncs with your Real-Debrid account. You can instantly view and manage the conversion directly from the **Torrents to Direct Download** page on the official Real-Debrid website.
* **Zero Hosting:** No copyrighted files, torrents, or media are ever hosted, stored, cached, or seeded by this application. All downloads are direct HTTP streams handled entirely by Real-Debrid's servers, keeping your local network completely detached from the P2P swarm.

---

## 📸 App Previews

**Main Interface & Recent Releases**
![Main UI Preview](<Main Interface & Recent Releases.png>)

**Most Popular Repacks of the Week**
![Most Popular](<Most Popular Repacks of the Week.png>)

**Upcoming Repacks Schedule**
![Upcoming Repacks](<Upcoming Repacks Schedule.png>)

**Integrated Search Functionality**
![Search](<Integrated Search Functionality.png>)

**Selective Downloading & File Management**
![Selective Download](<Selective Downloading & File Management.png>)

**Active Downloads & Speed Limiter**
![Downloads Manager](<Active Downloads & Speed Limiter.png>)

**Clean & Portable Local File Structure**
![Local Files](<Files created after starting exe.png>)

**Real-Debrid Dashboard Integration**
![Real-Debrid Torrents Page](<Real-Debrid Tracking .png>)

**Live Repack Features & File Selection**
![Repack Details](<Details.png>)

**Live Repack Features & File Selection**
![Repack Details](<Details 2.png>)

---

## 💖 Support the Original Creator
* **Support FitGirl:** This tool interacts with data provided by FitGirl Repacks. If you appreciate her incredible work, please consider supporting her directly by visiting the official [FitGirl Repacks Donations Page](https://fitgirl-repacks.site/donations/) to donate.

---

*Disclaimer: This project is an independent, open-source client application designed solely to interface with Real-Debrid and public web data. The author does not host, store, cache, upload, or distribute any ROMs, media, torrents, or copyrighted content on any server. All data processing and direct downloads are handled entirely via third-party services and the user's personal Real-Debrid account. This tool is provided "as is" without warranty of any kind.*
