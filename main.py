# =====================================================================
# --- IMPORTS & DEPENDENCIES ---
# =====================================================================
import os
import sys
from ui.main_window import MainWindow


# =====================================================================
# --- RESOURCE PATH UTILITY ---
# =====================================================================
def resource_path(relative_path):
    """Get absolute path to resource, works for development and PyInstaller bundles."""
    try:
        # PyInstaller creates a temp folder and stores the path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# =====================================================================
# --- APPLICATION ENTRY POINT ---
# =====================================================================
if __name__ == "__main__":
    print("Launching Custom Game Downloader...")
    app = MainWindow()
    
    # Apply application window icon
    app.iconbitmap(resource_path("Fitgirl.ico"))
    
    app.mainloop()