#!/usr/bin/env python3
"""
AiPi-MemoryCore Dashboard Launcher
Launches uvicorn server and opens centered browser window.
"""

import os
import sys
import time
import webbrowser
import subprocess
from pathlib import Path

# ────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}/docs"

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900

# ────────────────────────────────────────────────────────────────


def get_screen_size():
    """Get screen dimensions (Windows)."""
    try:
        import ctypes

        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except Exception:
        return 1920, 1080  # Default fallback


def center_window_geometry():
    """Calculate centered window position."""
    screen_w, screen_h = get_screen_size()
    x = (screen_w - WINDOW_WIDTH) // 2
    y = (screen_h - WINDOW_HEIGHT) // 2
    return x, y


def open_centered_browser():
    """Open browser with centered window (Chrome/Edge with app mode)."""
    x, y = center_window_geometry()

    # Try Chrome app mode first (cleanest UI)
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    ]

    for chrome_path in chrome_paths:
        if Path(chrome_path).exists():
            try:
                subprocess.Popen([
                    chrome_path,
                    f"--app={URL}",
                    f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}",
                    f"--window-position={x},{y}",
                    "--new-window",
                ])
                    print(f"Opened Chrome app window at ({x}, {y})")                return
            except Exception as e:
                    print(f"Chrome app mode failed: {e}")    
    # Fallback: default browser (won't be centered)
    print("Chrome not found, opening default browser...")    webbrowser.open(URL)


def launch_server():
    """Start uvicorn server in background."""
    print(f"🚀 Starting AiPi-MemoryCore dashboard server on {HOST}:{PORT}...")   
    # Change to repo root
    repo_root = Path(__file__).parent
    os.chdir(repo_root)

    # Start uvicorn (inherit stdout/stderr so pipe buffers can't block uvicorn)
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "dashboard.app:app",
            "--host",
            HOST,
            "--port",
            str(PORT),
            "--reload",
        ],
    )

    # Wait for server to be ready
    print("⏳ Waiting for server to start...")
    time.sleep(3)

    return server


def main():
    print("""
╭────────────────────────────────────────────────────────────╮
│  AiPi-MemoryCore Dashboard Launcher                      │
│  Phase 1-5 memory architecture                          │
╰────────────────────────────────────────────────────────────╯
    """)

    server = None
    try:
        # Launch FastAPI server
        server = launch_server()

        # Open centered browser window
        open_centered_browser()

        print(f"\n✅ Dashboard running at {URL}")
        print("\n🛡️  Press Ctrl+C to stop the server")
        print("─" * 60)

        # Keep server running
        server.wait()

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down server...")
        if server is not None:
            server.terminate()
            server.wait()
        print("✅ Server stopped.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
