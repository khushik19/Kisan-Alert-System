"""
start_server.py — One-command startup for the Kisan Alert advisory backend.

Usage:
    python start_server.py

What it does:
  1. Starts the FastAPI server (uvicorn) on port 8000
  2. Opens a localtunnel (no ngrok account needed) to make it public
  3. Prints the public URL for Person 2 to put in their .env as ADVISORY_ENGINE_URL

Keep this terminal open during the hackathon demo.
"""

import subprocess
import sys
import threading
import time
import os

PORT = 8000

def run_server():
    venv_uvicorn = os.path.join(os.path.dirname(__file__), "venv", "Scripts", "uvicorn.exe")
    subprocess.run([venv_uvicorn, "main:app", "--port", str(PORT), "--reload"])

def run_tunnel():
    time.sleep(3)  # Let the server start first
    try:
        from pyngrok import ngrok
        tunnel = ngrok.connect(PORT)
        url = tunnel.public_url
        if url.startswith("http://"):
            url = url.replace("http://", "https://")
        print("\n" + "="*60)
        print(f"  PUBLIC URL (ngrok): {url}/advisory")
        print(f"  Tell Person 2 to set in voice_telephony/.env:")
        print(f"  ADVISORY_ENGINE_URL={url}/advisory")
        print("="*60 + "\n")
    except Exception:
        # pyngrok unavailable / blocked — fall back to localtunnel via Node
        result = subprocess.run(
            ["npx", "-y", "localtunnel", "--port", str(PORT)],
            capture_output=True, text=True, timeout=30
        )
        for line in result.stdout.splitlines():
            if "loca.lt" in line or "your url" in line.lower():
                url = line.split("url is:")[-1].strip()
                print("\n" + "="*60)
                print(f"  PUBLIC URL (localtunnel): {url}/advisory")
                print(f"  Tell Person 2 to set in voice_telephony/.env:")
                print(f"  ADVISORY_ENGINE_URL={url}/advisory")
                print("="*60 + "\n")

if __name__ == "__main__":
    print(f"Starting Kisan Alert Advisory Engine on port {PORT}...")
    t = threading.Thread(target=run_tunnel, daemon=True)
    t.start()
    run_server()
