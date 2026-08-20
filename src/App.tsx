import { useState, useEffect } from "react";
import { invoke } from '@tauri-apps/api/core';
import "./App.css";

const themes = {
  obsidian: {
    name: "Pure Obsidian",
    bg: "#000000",
    cardBg: "#121212",
    panelBg: "#1a1a1a",
    border: "rgba(255, 255, 255, 0.08)",
    accent: "#e2e8f0",
    accentHover: "#ffffff",
    text: "#94a3b8",
    titleText: "#ffffff",
    glow: "rgba(226, 232, 240, 0.3)",
  },
  steam: {
    name: "Midnight Steam",
    bg: "#1b2838",
    cardBg: "#171a21",
    panelBg: "#2a475e",
    border: "rgba(102, 192, 244, 0.15)",
    accent: "#66c0f4",
    accentHover: "#417a9b",
    text: "#c7d5e0",
    titleText: "#ffffff",
    glow: "rgba(102, 192, 244, 0.4)",
  },
  emerald: {
    name: "Dark Emerald",
    bg: "#0e1111",
    cardBg: "#161b1b",
    panelBg: "#1f2626",
    border: "rgba(16, 185, 129, 0.15)",
    accent: "#10b981",
    accentHover: "#059669",
    text: "#9ca3af",
    titleText: "#f9fafb",
    glow: "rgba(16, 185, 129, 0.4)",
  },
  crimson: {
    name: "Crimson Void",
    bg: "#0b090f",
    cardBg: "#15121f",
    panelBg: "#201a2e",
    border: "rgba(244, 63, 94, 0.15)",
    accent: "#f43f5e",
    accentHover: "#e11d48",
    text: "#a1a1aa",
    titleText: "#fafafa",
    glow: "rgba(244, 63, 94, 0.4)",
  }
};

function App() {
  const [currentView, setCurrentView] = useState("recent");
  const [selectedGame, setSelectedGame] = useState<any>(null);
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("rd_api_key") || "");
  const [rdStatus, setRdStatus] = useState("Checking...");
  const [siteStatus, setSiteStatus] = useState("Checking...");
  
  const [toast, setToast] = useState<{ message: string; type?: "info" | "success" | "error" } | null>(null);

  const showToast = (message: string, type: "info" | "success" | "error" = "info") => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 3500);
  };

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [recent, setRecent] = useState<any[]>([]);
  const [recentPage, setRecentPage] = useState(1);
  const [popular, setPopular] = useState<any[]>([]);
  const [upcoming, setUpcoming] = useState<any[]>([]);
  const [downloads, setDownloads] = useState<any[]>([]);
  const [speedLimit, setSpeedLimit] = useState("250");
  const [loading, setLoading] = useState(false);

  const [currentThemeKey, setCurrentThemeKey] = useState(() => localStorage.getItem("app_theme") || "steam");
  const t = themes[currentThemeKey as keyof typeof themes] || themes.steam;

  const [minimizeToTray, setMinimizeToTray] = useState(() => localStorage.getItem("minimize_to_tray") === "true");

  // Sync saved tray setting with backend on startup
  useEffect(() => {
    const savedMinimize = localStorage.getItem("minimize_to_tray") === "true";
    invoke('set_tray_setting', { minToTray: savedMinimize }).catch(() => {});
  }, []);

  const [networkHistory, setNetworkHistory] = useState<number[]>(Array(25).fill(0));
  const [peakSpeed, setPeakSpeed] = useState<number>(0);

  const [activeDownloadImage, setActiveDownloadImage] = useState<string>(() => localStorage.getItem("active_download_banner") || "");

  const [history, setHistory] = useState<any[]>([]);
  const [historyPage, setHistoryPage] = useState(1);
  const itemsPerPage = 6;

  const [gameDetailsData, setGameDetailsData] = useState<any>(null);
  const [loadingGameDetails, setLoadingGameDetails] = useState(false);
  const [activeGalleryImage, setActiveGalleryImage] = useState<string>("");

  const [torrentDialog, setTorrentDialog] = useState<any>(null);
  const [loadingTorrent, setLoadingTorrent] = useState(false);

  useEffect(() => {
    fetchSiteStatus();
    fetchRecentPage(1, false);
    fetchPopularAndUpcoming();
    
    const savedKey = localStorage.getItem("rd_api_key");
    if (savedKey) {
      setApiKey(savedKey);
      verifyRdAccount(savedKey);
    } else {
      setRdStatus("Invalid Key");
    }

    const interval = setInterval(() => {
      fetch("http://127.0.0.1:8000/api/downloads/active")
        .then((res) => res.json())
        .then((data) => {
          if (data && typeof data === "object") {
            const list = Object.keys(data).map((id) => ({
              id,
              ...data[id]
            }));
            setDownloads(list);

            if (list.length > 0) {
              const activeItem = list[0];
              if (activeItem.speed !== undefined) {
                const currentSpeed = activeItem.speed || 0;
                setPeakSpeed((prev) => Math.max(prev, currentSpeed));
                setNetworkHistory((prev) => [...prev.slice(1), currentSpeed]);
              } else {
                setNetworkHistory((prev) => [...prev.slice(1), 0]);
              }

              if (activeItem.filename && !activeDownloadImage && !localStorage.getItem("active_download_banner")) {
                const cleanName = activeItem.filename
                  .replace(/\[.*?\]/g, "")
                  .replace(/\(.*?\)/g, "")
                  .replace(/\.(rar|zip|exe|7z)$/i, "")
                  .trim();
                
                fetch("http://127.0.0.1:8000/api/banner", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ title: cleanName }),
                })
                  .then((r) => r.json())
                  .then((bData) => {
                    if (bData && bData.banner_url) {
                      setActiveDownloadImage(bData.banner_url);
                      localStorage.setItem("active_download_banner", bData.banner_url);
                    }
                  })
                  .catch(() => {});
              }
            } else {
              setNetworkHistory((prev) => [...prev.slice(1), 0]);
              setActiveDownloadImage("");
              localStorage.removeItem("active_download_banner");
            }
          }
        })
        .catch(() => {});
    }, 1000);

    return () => clearInterval(interval);
  }, [activeDownloadImage]);

  const changeTheme = (key: string) => {
    setCurrentThemeKey(key);
    localStorage.setItem("app_theme", key);
    showToast("Theme updated successfully", "success");
  };

  const toggleMinimizeToTray = async (val: boolean) => {
    setMinimizeToTray(val);
    localStorage.setItem("minimize_to_tray", val.toString());
    try {
      await invoke('set_tray_setting', { minToTray: val });
    } catch (err) {
      console.error("Failed to update tray settings in the backend:", err);
    }
    showToast(val ? "Minimize to tray enabled" : "Minimize to tray disabled", "info");
  };

  const fetchSiteStatus = () => {
    fetch("http://127.0.0.1:8000/api/status")
      .then((res) => res.json())
      .then((data) => setSiteStatus(data.site_up ? "Online" : "Offline"))
      .catch(() => setSiteStatus("Offline"));
  };

  const fetchRecentPage = (pageNum: number, force = false) => {
    const targetPage = Math.max(1, Math.min(pageNum, 790));
    const suffix = force ? `?page=${targetPage}&force=true` : `?page=${targetPage}`;
    if (force) showToast(`Fetching page ${targetPage} of 790...`, "info");
    
    fetch(`http://127.0.0.1:8000/api/recent${suffix}`)
      .then((res) => res.json())
      .then((data) => {
        const newData = Array.isArray(data) ? data : [];
        setRecent(newData);
        setRecentPage(targetPage);
      })
      .catch((err) => console.error(err));
  };

  const fetchPopularAndUpcoming = (force = false) => {
    const suffix = force ? "?force=true" : "";
    fetch(`http://127.0.0.1:8000/api/popular${suffix}`)
      .then((res) => res.json())
      .then((data) => setPopular(Array.isArray(data) ? data : []))
      .catch((err) => console.error(err));

    fetch("http://127.0.0.1:8000/api/upcoming")
      .then((res) => res.json())
      .then((data) => setUpcoming(Array.isArray(data) ? data : []))
      .catch((err) => console.error(err));
  };

  const verifyRdAccount = async (key: string) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/account", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ magnet: "", api_key: key }),
      });
      const data = await res.json();
      if (res.ok && data.active) {
        setRdStatus(`Active (${data.type})`);
      } else {
        setRdStatus("Invalid Key");
      }
    } catch {
      setRdStatus("Error");
    }
  };

  const saveApiKey = () => {
    const trimmedKey = apiKey.trim();
    if (trimmedKey) {
      localStorage.setItem("rd_api_key", trimmedKey);
      verifyRdAccount(trimmedKey);
      showToast("API key stored securely.", "success");
    } else {
      localStorage.removeItem("rd_api_key");
      setRdStatus("Invalid Key");
      showToast("API key cleared.", "error");
    }
  };

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query) return;
    setLoading(true);
    setSelectedGame(null);
    setCurrentView("search");
    try {
      const response = await fetch("http://127.0.0.1:8000/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await response.json();
      setResults(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function applySpeedLimit() {
    try {
      const limitVal = parseFloat(speedLimit) || 0;
      const res = await fetch("http://127.0.0.1:8000/api/speed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ speed_limit: limitVal }),
      });
      if (res.ok) {
        showToast(`Bandwidth rate cap set to ${limitVal} Mbps.`, "success");
      } else {
        showToast("Failed to update rate cap.", "error");
      }
    } catch (err) {
      showToast("Error communicating with backend.", "error");
    }
  }

  async function openGamePage(item: any) {
    setSelectedGame(item);
    setLoadingGameDetails(true);
    setGameDetailsData(null);
    setActiveGalleryImage(item.image || "");

    const targetUrl = item.url || item.link;
    if (!targetUrl) {
      setLoadingGameDetails(false);
      return;
    }

    try {
      const res = await fetch("http://127.0.0.1:8000/api/details", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: targetUrl }),
      });
      const data = await res.json();
      setGameDetailsData(data.items || []);
      
      const firstImage = (data.items || []).find((i: any) => i.type === 'image');
      if (firstImage && firstImage.url) {
        setActiveGalleryImage(firstImage.url);
      }
    } catch (err) {
      console.error("Failed to load internal game details:", err);
    } finally {
      setLoadingGameDetails(false);
    }
  }

  async function handleDownload(item: any) {
    const key = localStorage.getItem("rd_api_key") || apiKey;
    if (!key) {
      showToast("Please input and save your Real-Debrid API Key first.", "error");
      return;
    }
    const magnet = item.magnet || item.link || item.url;
    if (!magnet) {
      showToast("No valid download source found.", "error");
      return;
    }

    const rawTitle = item.title || item.name || "Unknown Game";
    const cleanTitle = rawTitle
      .replace(/\[.*?\]/g, "")
      .replace(/\(.*?\)/g, "")
      .replace(/\.(rar|zip|exe|7z)$/i, "")
      .trim();

    try {
      const bannerRes = await fetch("http://127.0.0.1:8000/api/banner", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: cleanTitle }),
      });
      const bannerData = await bannerRes.json();
      if (bannerRes.ok && bannerData.banner_url) {
        setActiveDownloadImage(bannerData.banner_url);
        localStorage.setItem("active_download_banner", bannerData.banner_url);
      } else if (item.image) {
        setActiveDownloadImage(item.image);
        localStorage.setItem("active_download_banner", item.image);
      }
    } catch (err) {
      if (item.image) {
        setActiveDownloadImage(item.image);
        localStorage.setItem("active_download_banner", item.image);
      }
    }

    setLoadingTorrent(true);
    showToast(`Resolving manifest for ${rawTitle}...`, "info");
    try {
      const response = await fetch("http://127.0.0.1:8000/api/torrent/info", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ magnet, api_key: key }),
      });
      const data = await response.json();
      if (response.ok && data && data.files) {
        const filesWithState = data.files.map((f: any) => ({ ...f, checked: true }));
        setTorrentDialog({
          id: data.id,
          filename: data.filename,
          files: filesWithState,
          image: data.banner_url || activeDownloadImage || item.image || ""
        });
      } else {
        showToast(data.detail || "Failed to retrieve torrent info.", "error");
      }
    } catch (err) {
      showToast("Error connecting to backend server.", "error");
    } finally {
      setLoadingTorrent(false);
    }
  }

  async function confirmTorrentSelection() {
    if (!torrentDialog) return;
    const selectedIds = torrentDialog.files
      .filter((f: any) => f.checked)
      .map((f: any) => f.id);

    if (torrentDialog.image) {
      setActiveDownloadImage(torrentDialog.image);
      localStorage.setItem("active_download_banner", torrentDialog.image);
    }

    showToast("Adding files to transfer queue...", "info");
    try {
      await fetch("http://127.0.0.1:8000/api/torrent/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          torrent_id: torrentDialog.id,
          selected_files: selectedIds,
          api_key: apiKey,
          speed_limit: parseFloat(speedLimit) || null,
          image: torrentDialog.image || ""
        }),
      });
      showToast("Download sequence initiated.", "success");
      setTorrentDialog(null);
    } catch (err) {
      showToast("Failed to start queue.", "error");
    } finally {
      setTorrentDialog(null);
    }
  }

  async function controlDownload(action: string, downloadId: string) {
    try {
      await fetch(`http://127.0.0.1:8000/api/downloads/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ download_id: downloadId }),
      });
      if (action === "stop") {
        setActiveDownloadImage("");
        localStorage.removeItem("active_download_banner");
      }
      showToast(`Download ${action}ed.`, "info");
    } catch (err) {
      console.error(err);
    }
  }

  async function openFolder(path: string) {
    try {
      await fetch("http://127.0.0.1:8000/api/history/open", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path }),
      });
    } catch (err) {
      console.error(err);
    }
  }

  async function deleteHistoryItem(index: number) {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/history/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ index }),
      });
      const data = await res.json();
      if (res.ok && Array.isArray(data.history)) {
        setHistory(data.history);
        showToast("History item removed.", "info");
      }
    } catch (err) {
      console.error(err);
    }
  }

  const getDisplayList = () => {
    if (currentView === "search") return results;
    if (currentView === "popular") return popular;
    if (currentView === "upcoming") return upcoming;
    return recent;
  };

  const getCleanGameTitle = (rawTitle: string) => {
    if (!rawTitle) return "";
    let clean = rawTitle;
    clean = clean.replace(/^#\d+\s+/, "").replace(/\[.*?\]/g, "");
    const splitTokens = [", v", " – v", " - v", ", Build", " – Build", " - Build", " v1.", " v2.", " + ", " – DLC", " - DLC"];
    for (const token of splitTokens) {
      const idx = clean.indexOf(token);
      if (idx !== -1) {
        clean = clean.substring(0, idx);
      }
    }
    return clean.trim();
  };

  const totalPages = Math.ceil(history.length / itemsPerPage) || 1;
  const paginatedHistory = history.slice((historyPage - 1) * itemsPerPage, historyPage * itemsPerPage);

  const activeDownload = downloads.length > 0 ? downloads[0] : null;
  const queuedDownloads = downloads.slice(1);
  const currentBannerImage = activeDownload?.image || activeDownloadImage || localStorage.getItem("active_download_banner") || "";

  const maxGraphVal = Math.max(...networkHistory, 1);
  const chartPoints = networkHistory.map((val, i) => {
    const x = 750 - (i / (networkHistory.length - 1)) * 400;
    const y = 65 - (val / maxGraphVal) * 45;
    return `${x},${Math.max(15, Math.min(65, y))}`;
  }).join(" ");

  const scrapedImages = gameDetailsData ? gameDetailsData.filter((i: any) => i.type === 'image').map((i: any) => i.url) : [];

  const isRdActive = rdStatus.includes("Active");
  const isSiteOnline = siteStatus === "Online";

  return (
    <div style={{ display: "flex", height: "100vh", background: t.bg, color: t.text, fontFamily: "'Outfit', Segoe UI, -apple-system, sans-serif", overflow: "hidden", transition: "background 0.3s ease", position: "relative" }}>
      
      {/* Sleek Rounded Sidebar */}
      <div style={{ width: "240px", background: t.cardBg, padding: "24px 16px", display: "flex", flexDirection: "column", borderRight: `1px solid ${t.border}`, transition: "background 0.3s ease" }}>
        
        {/* Brand Header with Full Project Name */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "22px", paddingLeft: "4px" }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: t.accent, boxShadow: `0 0 12px ${t.glow}`, flexShrink: 0 }}></div>
          <h2 style={{ fontSize: "11px", fontWeight: "700", letterSpacing: "0.5px", textTransform: "uppercase", color: t.titleText, margin: 0, lineHeight: "1.3" }}>
            FitGirl Repacks Real Debrid Downloader
          </h2>
        </div>
        
        {/* Status Box with Indicators */}
        <div style={{ background: t.panelBg, border: `1px solid ${t.border}`, borderRadius: "14px", padding: "12px 14px", marginBottom: "16px", fontSize: "11px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ color: t.text }}>Real-Debrid</span>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: isRdActive ? "#10b981" : "#f87171", boxShadow: `0 0 8px ${isRdActive ? "#10b981" : "#f87171"}` }}></div>
              <span style={{ color: isRdActive ? t.accent : "#f87171", fontWeight: "600" }}>{rdStatus}</span>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ color: t.text }}>FitGirl Site</span>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: isSiteOnline ? "#10b981" : "#f87171", boxShadow: `0 0 8px ${isSiteOnline ? "#10b981" : "#f87171"}` }}></div>
              <span style={{ color: isSiteOnline ? t.accent : "#f87171", fontWeight: "600" }}>{siteStatus}</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: "flex", flexDirection: "column", gap: "4px", flex: 1 }}>
          <div style={{ fontSize: "10px", fontWeight: "600", color: "#475569", letterSpacing: "0.8px", textTransform: "uppercase", margin: "6px 0 6px 4px" }}>Navigation</div>
          {[
            { id: "recent", label: "Recent Repacks" },
            { id: "popular", label: "Most Popular of the week" },
            { id: "upcoming", label: "Upcoming Repacks" },
            { id: "downloads", label: "Active Download Que" },
            { id: "library", label: "Download History" },
            { id: "settings", label: "Settings" }
          ].map((tab) => {
            const isActive = !selectedGame && currentView === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setSelectedGame(null);
                  setCurrentView(tab.id);
                  if (tab.id === "library") {
                    setHistoryPage(1);
                    fetch("http://127.0.0.1:8000/api/history")
                      .then((res) => res.json())
                      .then((data) => setHistory(Array.isArray(data) ? data : []))
                      .catch((err) => console.error(err));
                  }
                }}
                style={{
                  padding: "9px 14px",
                  background: isActive ? t.panelBg : "transparent",
                  color: isActive ? t.accent : t.text,
                  border: "none",
                  borderRadius: "10px",
                  textAlign: "left",
                  cursor: "pointer",
                  fontWeight: isActive ? "600" : "500",
                  fontSize: "12px",
                  transition: "all 0.2s"
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* App Version Footer Tag */}
        <div style={{ padding: "8px 4px 0 4px", borderTop: `1px solid ${t.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "10px", color: t.text, opacity: 0.7 }}>
          <span>Client Version</span>
          <span style={{ fontWeight: "600", color: t.titleText }}>v1.0.3</span>
        </div>

      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: t.bg, position: "relative" }}>
        
        {/* Top Navbar */}
        <div style={{ padding: "14px 28px", background: t.cardBg, borderBottom: `1px solid ${t.border}`, display: "flex", alignItems: "center", gap: "16px" }}>
          <form onSubmit={handleSearch} style={{ display: "flex", flex: 1, gap: "10px" }}>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search library archives..."
              style={{ flex: 1, padding: "8px 14px", background: t.panelBg, border: `1px solid ${t.border}`, color: t.titleText, borderRadius: "10px", fontSize: "12px", outline: "none" }}
            />
            <button type="submit" style={{ padding: "8px 20px", background: t.panelBg, color: t.titleText, border: `1px solid ${t.border}`, borderRadius: "10px", cursor: "pointer", fontWeight: "600", fontSize: "12px" }}>
              {loading ? "Searching..." : "Search"}
            </button>
          </form>
          <button onClick={() => {
            if (currentView === 'recent') fetchRecentPage(recentPage, true);
            else fetchPopularAndUpcoming(true);
          }} style={{ padding: "8px 14px", background: t.panelBg, color: t.text, border: `1px solid ${t.border}`, borderRadius: "10px", cursor: "pointer", fontSize: "11px" }}>Refresh</button>
        </div>

        {/* View Container */}
        <div style={{ flex: 1, padding: "28px 48px", overflowY: "auto", background: t.bg, position: "relative" }}>
          {loadingTorrent && <div style={{ marginBottom: "18px", padding: "10px 14px", background: t.cardBg, border: `1px solid ${t.accent}`, borderRadius: "12px", fontSize: "11px", color: t.accent }}>Analyzing torrent metadata with Real-Debrid...</div>}
          
          {selectedGame ? (
            /* IMMERSIVE INTERNAL GAME PAGE */
            <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%", maxWidth: "1100px", margin: "0 auto" }}>
              
              {/* Back Button */}
              <div>
                <button onClick={() => setSelectedGame(null)} style={{ background: "transparent", border: "none", color: t.text, fontSize: "13px", fontWeight: "600", cursor: "pointer", display: "flex", alignItems: "center", gap: "6px", padding: 0 }}>
                  ← Back to Catalogue
                </button>
              </div>

              {/* HERO BANNER */}
              <div style={{ 
                position: "relative",
                width: "100%",
                height: "360px",
                backgroundColor: "#06070a",
                border: `1px solid ${t.border}`, 
                borderRadius: "16px", 
                display: "flex", 
                flexDirection: "column", 
                justifyContent: "flex-end",
                overflow: "hidden",
                boxShadow: "0 16px 40px rgba(0,0,0,0.7)"
              }}>
                {selectedGame.image && (
                  <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", zIndex: 0, pointerEvents: "none", overflow: "hidden" }}>
                    <img 
                      src={selectedGame.image} 
                      alt="" 
                      style={{ width: "100%", height: "100%", objectFit: "cover", filter: "blur(25px) brightness(0.35)", transform: "scale(1.2)" }} 
                    />
                    <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "calc(100% - 90px)", display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }}>
                      <img 
                        src={selectedGame.image} 
                        alt="" 
                        style={{ height: "100%", width: "auto", objectFit: "contain", maxWidth: "100%" }} 
                      />
                    </div>
                    <div style={{
                      position: "absolute",
                      top: 0, left: 0, width: "100%", height: "100%",
                      background: "linear-gradient(180deg, rgba(9,10,15,0.05) 30%, rgba(9,10,15,0.95) 85%)"
                    }} />
                  </div>
                )}

                {/* Title & Action Overlay Bar */}
                <div style={{ padding: "24px 32px", display: "flex", justifyContent: "space-between", alignItems: "flex-end", zIndex: 2, background: "rgba(9,10,15,0.85)", backdropFilter: "blur(8px)", borderTop: `1px solid ${t.border}` }}>
                  <div>
                    <h1 style={{ fontSize: "26px", fontWeight: "700", color: t.titleText, margin: "0 0 4px 0", textShadow: "0 2px 6px rgba(0,0,0,0.9)" }}>
                      {selectedGame.title || selectedGame.name}
                    </h1>
                    <p style={{ fontSize: "12px", color: t.text, margin: 0 }}>FitGirl Repack Verified</p>
                  </div>

                  <div style={{ display: "flex", gap: "10px", minWidth: "220px", justifyContent: "flex-end" }}>
                    {activeDownload ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: "6px", width: "100%" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: t.text }}>
                          <span>{activeDownload.status === "paused" ? "Paused" : `Downloading (${Math.round((activeDownload.progress || 0) * 100)}%)`}</span>
                          <span style={{ color: t.accent }}>{activeDownload.speed ? `${activeDownload.speed.toFixed(2)} Mbps` : "0 bps"}</span>
                        </div>
                        <div style={{ width: "100%", background: t.panelBg, height: "6px", borderRadius: "3px", overflow: "hidden" }}>
                          <div style={{ width: `${(activeDownload.progress || 0) * 100}%`, background: t.accent, height: "100%", transition: "width 0.3s ease" }}></div>
                        </div>
                        <div style={{ display: "flex", gap: "6px", marginTop: "2px" }}>
                          {activeDownload.status === "paused" ? (
                            <button onClick={() => controlDownload("resume", activeDownload.id)} style={{ flex: 1, padding: "5px", background: t.accent, color: "#000", border: "none", borderRadius: "6px", cursor: "pointer", fontSize: "11px", fontWeight: "700" }}>Resume</button>
                          ) : (
                            <button onClick={() => controlDownload("pause", activeDownload.id)} style={{ flex: 1, padding: "5px", background: t.panelBg, color: t.titleText, border: `1px solid ${t.border}`, borderRadius: "6px", cursor: "pointer", fontSize: "11px", fontWeight: "600" }}>Pause</button>
                          )}
                          <button onClick={() => controlDownload("stop", activeDownload.id)} style={{ padding: "5px 12px", background: "#7f1d1d", color: "#fca5a5", border: "none", borderRadius: "6px", cursor: "pointer", fontSize: "11px", fontWeight: "600" }}>Cancel</button>
                        </div>
                      </div>
                    ) : (
                      <button 
                        onClick={() => handleDownload(selectedGame)} 
                        style={{ padding: "10px 24px", background: t.accent, color: "#000", border: "none", borderRadius: "10px", cursor: "pointer", fontWeight: "700", fontSize: "13px", boxShadow: `0 4px 14px ${t.glow}`, transition: "background 0.2s" }}
                        onMouseEnter={(e) => e.currentTarget.style.background = t.accentHover}
                        onMouseLeave={(e) => e.currentTarget.style.background = t.accent}>
                        Download
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* DEDICATED SCREENSHOT PREVIEW BOX & CAROUSEL STRIP */}
              {scrapedImages.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: "16px", padding: "20px" }}>
                  
                  {/* Dedicated Main Preview Player Frame */}
                  <div style={{ width: "100%", height: "380px", borderRadius: "12px", overflow: "hidden", background: "#06070a", border: `1px solid ${t.border}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <img 
                      src={activeGalleryImage || scrapedImages[0]} 
                      alt="" 
                      style={{ width: "100%", height: "100%", objectFit: "contain", transition: "opacity 0.2s ease" }} 
                    />
                  </div>

                  {/* Thumbnail Carousel Strip */}
                  <div style={{ display: "flex", gap: "10px", overflowX: "auto", paddingBottom: "4px" }}>
                    {scrapedImages.map((imgUrl: string, imgIdx: number) => {
                      const isSelected = activeGalleryImage === imgUrl;
                      return (
                        <div 
                          key={imgIdx} 
                          onClick={() => setActiveGalleryImage(imgUrl)}
                          style={{ 
                            minWidth: "130px", 
                            height: "75px", 
                            borderRadius: "10px", 
                            overflow: "hidden", 
                            cursor: "pointer", 
                            border: isSelected ? `2px solid ${t.accent}` : `1px solid ${t.border}`,
                            opacity: isSelected ? 1 : 0.6,
                            transition: "all 0.2s ease"
                          }}>
                          <img src={imgUrl} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                        </div>
                      );
                    })}
                  </div>

                </div>
              )}

              {/* Scraped Features & Overview */}
              <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: "16px", padding: "28px", display: "flex", flexDirection: "column", gap: "12px" }}>
                <h3 style={{ fontSize: "14px", fontWeight: "600", color: t.titleText, margin: "0 0 10px 0", textTransform: "uppercase", letterSpacing: "0.5px" }}>Overview & Features</h3>
                {loadingGameDetails ? (
                  <div style={{ color: t.text, fontSize: "12px", padding: "20px 0" }}>Loading game details from indexer...</div>
                ) : gameDetailsData && gameDetailsData.length > 0 ? (
                  gameDetailsData.map((detailItem: any, dIdx: number) => {
                    if (detailItem.type === 'text') {
                      if (detailItem.content.trim() === "Screenshots:") return null;
                      const isHeader = ["Repack Features:", "Game Description:"].includes(detailItem.content);
                      return (
                        <div key={dIdx} style={{
                          fontSize: isHeader ? "13px" : "12px",
                          fontWeight: isHeader ? "600" : "400",
                          color: isHeader ? t.titleText : t.text,
                          lineHeight: "1.5",
                          whiteSpace: "pre-line",
                          marginTop: isHeader ? "12px" : "0"
                        }}>
                          {detailItem.content}
                        </div>
                      );
                    }
                    return null;
                  })
                ) : (
                  <div style={{ color: t.text, fontSize: "12px" }}>No additional description text found. Click download to fetch torrent package.</div>
                )}
              </div>

            </div>
          ) : currentView === "settings" ? (
            /* SETTINGS VIEW PAGE */
            <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%", maxWidth: "700px" }}>
              <h2 style={{ fontSize: "20px", fontWeight: "700", color: t.titleText, margin: 0 }}>Launcher Settings</h2>

              {/* Theme Settings Card */}
              <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: "16px", padding: "24px", display: "flex", flexDirection: "column", gap: "12px" }}>
                <h3 style={{ fontSize: "14px", fontWeight: "600", color: t.titleText, margin: 0 }}>Appearance & Themes</h3>
                <p style={{ fontSize: "12px", color: t.text, margin: 0 }}>Choose a color palette for your launcher interface.</p>
                <select 
                  value={currentThemeKey} 
                  onChange={(e) => changeTheme(e.target.value)}
                  style={{ width: "100%", padding: "10px 14px", background: t.panelBg, border: `1px solid ${t.border}`, color: t.titleText, borderRadius: "10px", fontSize: "12px", outline: "none", cursor: "pointer", marginTop: "6px" }}>
                  <option value="steam">Midnight Steam</option>
                  <option value="obsidian">Pure Obsidian</option>
                  <option value="emerald">Dark Emerald</option>
                  <option value="crimson">Crimson Void</option>
                </select>
              </div>

              {/* System Tray Behavior Preference Card */}
              <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: "16px", padding: "24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <h3 style={{ fontSize: "14px", fontWeight: "600", color: t.titleText, margin: 0 }}>Minimize to System Tray</h3>
                  <p style={{ fontSize: "12px", color: t.text, margin: 0 }}>Keep active background downloads running in the system tray when closed.</p>
                </div>
                <label style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
                  <input 
                    type="checkbox" 
                    checked={minimizeToTray} 
                    onChange={(e) => toggleMinimizeToTray(e.target.checked)} 
                    style={{ accentColor: t.accent, width: "16px", height: "16px", cursor: "pointer" }} 
                  />
                </label>
              </div>

              {/* API Token Settings Card */}
              <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: "16px", padding: "24px", display: "flex", flexDirection: "column", gap: "12px" }}>
                <h3 style={{ fontSize: "14px", fontWeight: "600", color: t.titleText, margin: 0 }}>Real-Debrid API Token</h3>
                <p style={{ fontSize: "12px", color: t.text, margin: 0 }}>Required for resolving torrent magnets and starting cloud downloads.</p>
                <div style={{ display: "flex", gap: "10px", marginTop: "6px" }}>
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Paste Real-Debrid API token..."
                    style={{ flex: 1, padding: "10px 14px", background: t.panelBg, border: `1px solid ${t.border}`, color: t.titleText, borderRadius: "10px", fontSize: "12px", outline: "none" }}
                  />
                  <button onClick={saveApiKey} style={{ padding: "10px 20px", background: t.panelBg, color: t.titleText, border: `1px solid ${t.border}`, borderRadius: "10px", cursor: "pointer", fontWeight: "600", fontSize: "12px", transition: "background 0.2s" }}>
                    Save Key
                  </button>
                </div>
              </div>

              {/* Speed Limit Settings Card */}
              <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: "16px", padding: "24px", display: "flex", flexDirection: "column", gap: "12px" }}>
                <h3 style={{ fontSize: "14px", fontWeight: "600", color: t.titleText, margin: 0 }}>Bandwidth Speed Limit</h3>
                <p style={{ fontSize: "12px", color: t.text, margin: 0 }}>Set a maximum transfer rate cap in Mbps for active queue tasks.</p>
                <div style={{ display: "flex", gap: "10px", alignItems: "center", marginTop: "6px" }}>
                  <input 
                    value={speedLimit} 
                    onChange={(e) => setSpeedLimit(e.target.value)} 
                    style={{ width: "90px", padding: "10px", background: t.panelBg, border: `1px solid ${t.border}`, color: t.titleText, borderRadius: "10px", textAlign: "center", fontSize: "12px", outline: "none" }} 
                  />
                  <span style={{ fontSize: "12px", color: t.text }}>Mbps</span>
                  <button onClick={applySpeedLimit} style={{ marginLeft: "10px", padding: "10px 20px", background: t.panelBg, color: t.titleText, border: `1px solid ${t.border}`, borderRadius: "10px", cursor: "pointer", fontWeight: "600", fontSize: "12px" }}>
                    Apply Limit
                  </button>
                </div>
              </div>

              {/* Clear Stored Data & API Key Card */}
              <div style={{ background: t.cardBg, border: "1px solid rgba(248, 113, 113, 0.2)", borderRadius: "16px", padding: "24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <h3 style={{ fontSize: "14px", fontWeight: "600", color: "#f87171", margin: 0 }}>Clear Stored Data & API Key</h3>
                  <p style={{ fontSize: "12px", color: t.text, margin: 0 }}>Wipe your saved Real-Debrid token and local cache before removing the application.</p>
                </div>
                <button 
                  onClick={() => {
                    localStorage.clear();
                    setApiKey("");
                    setRdStatus("Invalid Key");
                    showToast("All local data and API keys cleared.", "success");
                  }}
                  style={{ padding: "8px 16px", background: "rgba(248, 113, 113, 0.1)", color: "#f87171", border: "1px solid rgba(248, 113, 113, 0.3)", borderRadius: "8px", cursor: "pointer", fontWeight: "600", fontSize: "11px", transition: "background 0.2s", whiteSpace: "nowrap" }}
                  onMouseEnter={(e) => e.currentTarget.style.background = "rgba(248, 113, 113, 0.2)"}
                  onMouseLeave={(e) => e.currentTarget.style.background = "rgba(248, 113, 113, 0.1)"}
                >
                  Clear Data
                </button>
              </div>

            </div>
          ) : currentView === "downloads" ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%" }}>
              
              {/* Active Download Hero Panel */}
              <div style={{ 
                position: "relative",
                width: "100%",
                height: "170px",
                backgroundColor: t.cardBg,
                border: `1px solid ${t.border}`, 
                borderRadius: "16px", 
                display: "flex", 
                flexDirection: "column", 
                justifyContent: "space-between",
                overflow: "hidden",
                boxShadow: "0 10px 30px rgba(0,0,0,0.5)"
              }}>
                
                {currentBannerImage && (
                  <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", zIndex: 0, pointerEvents: "none" }}>
                    <img 
                      src={currentBannerImage} 
                      alt="" 
                      style={{ 
                        width: "100%", 
                        height: "100%", 
                        objectFit: "cover",
                        objectPosition: "right center"
                      }} 
                    />
                    <div style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      width: "100%",
                      height: "100%",
                      background: "linear-gradient(90deg, rgba(9,10,15,0.96) 20%, rgba(9,10,15,0.65) 60%, rgba(9,10,15,0.2) 90%)"
                    }} />
                  </div>
                )}

                {/* Graph Sparkline */}
                <div style={{ position: "absolute", top: "12px", left: "0", right: "0", height: "75px", pointerEvents: "none", opacity: 0.5, zIndex: 1, overflow: "hidden" }}>
                  <svg width="100%" height="75" viewBox="0 0 950 75" preserveAspectRatio="none" style={{ display: "block" }}>
                    <polyline fill="none" stroke={t.accent} strokeWidth="2" points={chartPoints} />
                  </svg>
                </div>

                {/* Header Stats */}
                <div style={{ padding: "20px 28px 0 28px", display: "flex", justifyContent: "space-between", alignItems: "flex-start", zIndex: 2 }}>
                  <div>
                    <h2 style={{ fontSize: "17px", fontWeight: "600", color: t.titleText, margin: "0" }}>
                      {activeDownload ? activeDownload.filename : "No Active Download"}
                    </h2>
                  </div>

                  <div style={{ display: "flex", gap: "24px", fontSize: "11px", color: t.text, textAlign: "right", background: "rgba(9,10,15,0.7)", padding: "6px 12px", borderRadius: "10px", border: `1px solid ${t.border}` }}>
                    <div>
                      <div style={{ textTransform: "uppercase", fontSize: "9px", letterSpacing: "0.5px" }}>Speed</div>
                      <div style={{ fontSize: "12px", fontWeight: "600", color: t.accent }}>{activeDownload ? `${activeDownload.speed ? activeDownload.speed.toFixed(2) : 0} Mbps` : "0 bps"}</div>
                    </div>
                    <div>
                      <div style={{ textTransform: "uppercase", fontSize: "9px", letterSpacing: "0.5px" }}>Peak</div>
                      <div style={{ fontSize: "12px", fontWeight: "600", color: t.titleText }}>{peakSpeed.toFixed(2)} Mbps</div>
                    </div>
                  </div>
                </div>

                {/* Progress & Actions */}
                <div style={{ padding: "14px 28px 16px 28px", background: t.cardBg, backdropFilter: "blur(8px)", borderTop: `1px solid ${t.border}`, display: "flex", flexDirection: "column", gap: "8px", zIndex: 2 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11px", color: t.text }}>
                    <span>{activeDownload ? (activeDownload.status === "paused" ? "Paused" : `ETA: ${activeDownload.eta || 0}s`) : "Standby"}</span>
                    <span style={{ fontWeight: "600", color: t.titleText }}>{activeDownload ? `${Math.round((activeDownload.progress || 0) * 100)}%` : "0%"}</span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                    <div style={{ flex: 1, background: t.panelBg, height: "5px", borderRadius: "3px", overflow: "hidden" }}>
                      <div style={{ width: `${activeDownload ? (activeDownload.progress || 0) * 100 : 0}%`, background: t.accent, height: "100%", transition: "width 0.3s ease" }}></div>
                    </div>

                    {activeDownload && (
                      <div style={{ display: "flex", gap: "6px" }}>
                        {activeDownload.status === "paused" ? (
                          <button onClick={() => controlDownload("resume", activeDownload.id)} style={{ padding: "5px 16px", background: t.accent, color: "#000", border: "none", borderRadius: "8px", cursor: "pointer", fontSize: "11px", fontWeight: "700" }}>Resume</button>
                        ) : (
                          <button onClick={() => controlDownload("pause", activeDownload.id)} style={{ padding: "5px 16px", background: t.panelBg, color: t.titleText, border: `1px solid ${t.border}`, borderRadius: "8px", cursor: "pointer", fontSize: "11px", fontWeight: "600" }}>Pause</button>
                        )}
                        <button onClick={() => controlDownload("stop", activeDownload.id)} style={{ padding: "5px 16px", background: "#7f1d1d", color: "#fca5a5", border: "1px solid rgba(248, 113, 113, 0.3)", borderRadius: "8px", cursor: "pointer", fontSize: "11px", fontWeight: "600" }}>Cancel</button>
                      </div>
                    )}
                  </div>
                </div>

              </div>

              {/* Up Next List */}
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <h3 style={{ fontSize: "11px", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.8px", color: t.text, margin: 0, borderBottom: `1px solid ${t.border}`, paddingBottom: "6px" }}>
                  Queue ({queuedDownloads.length})
                </h3>
                {queuedDownloads.length === 0 ? (
                  <div style={{ color: t.text, fontSize: "12px", padding: "4px 0" }}>Queue is empty</div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {queuedDownloads.map((dl, idx) => (
                      <div key={idx} style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: "12px", padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: "12px", color: t.titleText }}>{dl.filename}</span>
                        <button onClick={() => controlDownload("stop", dl.id)} style={{ padding: "4px 10px", background: t.panelBg, color: "#f87171", border: "none", borderRadius: "8px", cursor: "pointer", fontSize: "10px", fontWeight: "600" }}>Remove</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : currentView === "library" ? (
            <div style={{ width: "100%" }}>
              <h3 style={{ fontSize: "11px", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: "16px", color: t.text }}>Download History</h3>
              {history.length === 0 ? (
                <div style={{ color: t.text, fontSize: "12px" }}>No download history recorded.</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {paginatedHistory.map((item, index) => {
                      const absoluteIndex = (historyPage - 1) * itemsPerPage + index;
                      return (
                        <div key={absoluteIndex} style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: "12px", padding: "14px 18px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <div>
                            <div style={{ fontSize: "13px", fontWeight: "600", color: t.titleText, marginBottom: "3px" }}>{item.filename}</div>
                            <div style={{ fontSize: "11px", color: t.text }}>Completed: {item.date}</div>
                          </div>
                          <div style={{ display: "flex", gap: "8px" }}>
                            {item.path && (
                              <button onClick={() => openFolder(item.path)} style={{ padding: "6px 14px", background: t.panelBg, color: t.titleText, border: "none", borderRadius: "8px", cursor: "pointer", fontSize: "11px", fontWeight: "500" }}>
                                Open Folder
                              </button>
                            )}
                            <button onClick={() => deleteHistoryItem(absoluteIndex)} style={{ padding: "6px 14px", background: t.panelBg, color: "#f87171", border: "none", borderRadius: "8px", cursor: "pointer", fontSize: "11px", fontWeight: "500" }}>
                              Delete
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {totalPages > 1 && (
                    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "12px", marginTop: "16px" }}>
                      <button onClick={() => setHistoryPage((p) => Math.max(p - 1, 1))} disabled={historyPage === 1} style={{ padding: "6px 14px", background: t.cardBg, color: historyPage === 1 ? t.text : t.titleText, border: `1px solid ${t.border}`, borderRadius: "8px", cursor: historyPage === 1 ? "not-allowed" : "pointer", fontSize: "11px" }}>Previous</button>
                      <span style={{ fontSize: "11px", color: t.text }}>Page {historyPage} of {totalPages}</span>
                      <button onClick={() => setHistoryPage((p) => Math.min(p + 1, totalPages))} disabled={historyPage === totalPages} style={{ padding: "6px 14px", background: t.cardBg, color: historyPage === totalPages ? t.text : t.titleText, border: `1px solid ${t.border}`, borderRadius: "8px", cursor: historyPage === totalPages ? "not-allowed" : "pointer", fontSize: "11px" }}>Next</button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : currentView === "upcoming" ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "12px", width: "100%" }}>
              {upcoming.map((item, index) => (
                <div key={index} style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: "12px", padding: "16px", display: "flex", alignItems: "center" }}>
                  <span style={{ fontSize: "12px", fontWeight: "500", color: t.titleText }}>{item.title}</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%", position: "relative" }}>
              
              {/* SIDE FLOATING ARROWS (Outside the main grid boundaries) */}
              {currentView === "recent" && (
                <>
                  {/* Right Arrow */}
                  <button 
                    onClick={() => fetchRecentPage(recentPage + 1)} 
                    disabled={recentPage >= 790}
                    title="Next Page"
                    style={{ 
                      position: "fixed", 
                      right: "16px", 
                      top: "50%", 
                      transform: "translateY(-50%)", 
                      width: "48px", 
                      height: "48px", 
                      borderRadius: "50%", 
                      background: t.cardBg, 
                      color: recentPage >= 790 ? t.text : t.titleText, 
                      border: `1px solid ${t.border}`, 
                      cursor: recentPage >= 790 ? "not-allowed" : "pointer", 
                      fontSize: "20px", 
                      fontWeight: "700", 
                      display: "flex", 
                      alignItems: "center", 
                      justifyContent: "center", 
                      backdropFilter: "blur(10px)",
                      boxShadow: "0 8px 24px rgba(0,0,0,0.8)",
                      opacity: recentPage >= 790 ? 0.2 : 0.4,
                      zIndex: 100,
                      transition: "all 0.2s ease"
                    }}
                    onMouseEnter={(e) => { if(recentPage < 790) { e.currentTarget.style.opacity = "1"; e.currentTarget.style.background = t.accent; e.currentTarget.style.color = "#000"; }}}
                    onMouseLeave={(e) => { e.currentTarget.style.opacity = recentPage >= 790 ? "0.2" : "0.4"; e.currentTarget.style.background = t.cardBg; e.currentTarget.style.color = t.titleText; }}>
                    →
                  </button>

                  {/* Left Arrow (Only visible if page > 1) */}
                  {recentPage > 1 && (
                    <button 
                      onClick={() => fetchRecentPage(recentPage - 1)} 
                      title="Previous Page"
                      style={{ 
                        position: "fixed", 
                        left: "258px", 
                        top: "50%", 
                        transform: "translateY(-50%)", 
                        width: "48px", 
                        height: "48px", 
                        borderRadius: "50%", 
                        background: t.cardBg, 
                        color: t.titleText, 
                        border: `1px solid ${t.border}`, 
                        cursor: "pointer", 
                        fontSize: "20px", 
                        fontWeight: "700", 
                        display: "flex", 
                        alignItems: "center", 
                        justifyContent: "center", 
                        backdropFilter: "blur(10px)",
                        boxShadow: "0 8px 24px rgba(0,0,0,0.8)",
                        opacity: 0.4,
                        zIndex: 100,
                        transition: "all 0.2s ease"
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.opacity = "1"; e.currentTarget.style.background = t.panelBg; }}
                      onMouseLeave={(e) => { e.currentTarget.style.opacity = "0.4"; e.currentTarget.style.background = t.cardBg; }}>
                      ←
                    </button>
                  )}
                </>
              )}

              {/* Game Cards Grid */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "18px" }}>
                {getDisplayList().map((item, index) => {
                  const rawTitle = item.title || item.name || "";
                  const displayName = getCleanGameTitle(rawTitle);
                  return (
                    <div key={index} style={{ 
                      position: "relative",
                      height: "320px", 
                      background: t.cardBg, 
                      border: `1px solid ${t.border}`, 
                      borderRadius: "16px", 
                      padding: "16px", 
                      display: "flex", 
                      flexDirection: "column", 
                      justifyContent: "flex-end", 
                      overflow: "hidden",
                      cursor: "pointer",
                      transition: "transform 0.2s, border-color 0.2s" 
                    }}
                         onClick={() => openGamePage(item)}
                         onMouseEnter={(e) => { e.currentTarget.style.borderColor = t.accentHover; e.currentTarget.style.transform = "translateY(-2px)"; }}
                         onMouseLeave={(e) => { e.currentTarget.style.borderColor = t.border; e.currentTarget.style.transform = "translateY(0)"; }}>
                      
                      {/* Background Full-Cover Artwork Image */}
                      {item.image ? (
                        <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", zIndex: 0 }}>
                          <img src={item.image} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                          <div style={{
                            position: "absolute",
                            top: 0, left: 0, width: "100%", height: "100%",
                            background: "linear-gradient(180deg, rgba(23,26,33,0.05) 10%, rgba(23,26,33,0.95) 75%)"
                          }} />
                        </div>
                      ) : (
                        <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", background: t.panelBg, zIndex: 0, display: "flex", alignItems: "center", justifyContent: "center", color: t.text, fontSize: "11px" }}>No Artwork</div>
                      )}

                      {/* Cleaned Game Name Overlay */}
                      <div style={{ position: "relative", zIndex: 1, paddingBottom: "4px" }}>
                        <h4 style={{ fontSize: "13px", fontWeight: "700", margin: 0, maxHeight: "54px", overflow: "hidden", textOverflow: "ellipsis", lineHeight: "1.4", color: t.titleText, textShadow: "0 2px 8px rgba(0,0,0,0.9)" }}>
                          {displayName}
                        </h4>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* BOTTOM PAGINATION BAR & PAGE INDICATOR */}
              {currentView === "recent" && (
                <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "16px", marginTop: "20px", paddingBottom: "16px" }}>
                  <button 
                    onClick={() => fetchRecentPage(recentPage - 1)} 
                    disabled={recentPage <= 1}
                    style={{ padding: "8px 18px", background: t.cardBg, color: recentPage <= 1 ? t.text : t.titleText, border: `1px solid ${t.border}`, borderRadius: "10px", cursor: recentPage <= 1 ? "not-allowed" : "pointer", fontSize: "12px", fontWeight: "600" }}>
                    Previous Page
                  </button>
                  <span style={{ fontSize: "13px", color: t.titleText, fontWeight: "700", background: t.cardBg, padding: "8px 16px", borderRadius: "10px", border: `1px solid ${t.border}` }}>
                    Page {recentPage} of 790
                  </span>
                  <button 
                    onClick={() => fetchRecentPage(recentPage + 1)} 
                    disabled={recentPage >= 790}
                    style={{ padding: "8px 18px", background: t.cardBg, color: recentPage >= 790 ? t.text : t.titleText, border: `1px solid ${t.border}`, borderRadius: "10px", cursor: recentPage >= 790 ? "not-allowed" : "pointer", fontSize: "12px", fontWeight: "600" }}>
                    Next Page
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Floating Toast Notification Popups */}
      {toast && (
        <div style={{
          position: "fixed",
          bottom: "24px",
          right: "24px",
          background: t.cardBg,
          border: `1px solid ${toast.type === "success" ? "#10b981" : toast.type === "error" ? "#f87171" : t.border}`,
          color: t.titleText,
          padding: "12px 20px",
          borderRadius: "12px",
          fontSize: "12px",
          fontWeight: "600",
          boxShadow: "0 10px 30px rgba(0,0,0,0.6)",
          zIndex: 2000,
          display: "flex",
          alignItems: "center",
          gap: "10px",
          animation: "fadeIn 0.2s ease"
        }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: toast.type === "success" ? "#10b981" : toast.type === "error" ? "#f87171" : t.accent }}></div>
          {toast.message}
        </div>
      )}

      {/* Torrent File Selection Modal */}
      {torrentDialog && (
        <div style={{ position: "fixed", top: 0, left: 0, width: "100vw", height: "100vh", background: "rgba(0, 0, 0, 0.8)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
          <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: "16px", width: "580px", maxHeight: "80vh", padding: "20px", display: "flex", flexDirection: "column" }}>
            <h3 style={{ margin: "0 0 6px 0", fontSize: "14px", fontWeight: "600", color: t.titleText }}>{torrentDialog.filename}</h3>
            <p style={{ fontSize: "11px", color: t.text, margin: "0 0 14px 0" }}>Select optional files and language packs to download:</p>
            
            <div style={{ flex: 1, overflowY: "auto", background: t.bg, border: `1px solid ${t.border}`, borderRadius: "10px", padding: "10px", marginBottom: "16px", display: "flex", flexDirection: "column", gap: "6px" }}>
              {torrentDialog.files.link ? null : torrentDialog.files.map((file: any, fIdx: number) => {
                const sizeMb = (file.bytes / (1024 * 1024)).toFixed(2);
                return (
                  <label key={fIdx} style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "11px", color: t.text, cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={file.checked}
                      onChange={(e) => {
                        const updated = [...torrentDialog.files];
                        updated[fIdx].checked = e.target.checked;
                        setTorrentDialog({ ...torrentDialog, files: updated });
                      }}
                      style={{ accentColor: t.accent, width: "13px", height: "13px" }}
                    />
                    <span style={{ flex: 1, wordBreak: "break-all" }}>{file.path} <span style={{ color: "#475569" }}>({sizeMb} MB)</span></span>
                  </label>
                );
              })}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
              <button onClick={() => setTorrentDialog(null)} style={{ padding: "7px 16px", background: t.panelBg, color: t.text, border: `1px solid ${t.border}`, borderRadius: "8px", cursor: "pointer", fontSize: "11px" }}>Cancel</button>
              <button onClick={confirmTorrentSelection} style={{ padding: "7px 18px", background: t.panelBg, color: t.titleText, border: `1px solid ${t.border}`, borderRadius: "8px", cursor: "pointer", fontWeight: "600", fontSize: "11px" }}>Start Download</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;