#!/usr/bin/env bash
set -e

echo "============================================"
echo "  destiny1-mk Setup (Linux)"
echo "============================================"
echo

# Check Python3 and pip3
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python3 not found."
    echo "Install with: sudo apt install python3 python3-pip"
    exit 1
fi
if ! command -v pip3 &>/dev/null; then
    echo "[ERROR] pip3 not found."
    echo "Install with: sudo apt install python3-pip"
    exit 1
fi

mkdir -p downloads

# ── Step 1: Python dependencies ──────────────────────────────────────────────
echo "[1/3] Installing Python dependencies..."
pip3 install -r requirements.txt
pip3 install -r requirements-linux.txt

# ── Step 2: uinput (Linux equivalent of ViGEmBus) ────────────────────────────
echo
echo "[2/3] Configuring uinput virtual controller support..."
sudo modprobe uinput
# /etc/modules exists on Debian/Ubuntu; other distros use different persistence paths
if [ -f /etc/modules ] && ! grep -qxF "uinput" /etc/modules; then
    echo "uinput" | sudo tee -a /etc/modules > /dev/null
fi
# Give the input group write access to uinput
sudo chown root:input /dev/uinput 2>/dev/null && sudo chmod 660 /dev/uinput || sudo chmod 666 /dev/uinput
if ! id -nG "$USER" | grep -qw "input"; then
    echo "Adding $USER to 'input' group (log out and back in for it to take effect)..."
    sudo usermod -aG input "$USER"
    echo "[!] Log out and back in, then re-run this script."
fi
echo "uinput ready."

# ── Step 3: chiaki-ng Linux build ─────────────────────────────────────────────
echo
echo "[3/3] Downloading chiaki-ng for Linux..."

DOWNLOAD_URL=$(python3 - <<'PYEOF'
import urllib.request, json, sys

req = urllib.request.urlopen("https://api.github.com/repos/streetpea/chiaki-ng/releases/latest")
data = json.loads(req.read())
assets = data.get("assets", [])

# Prefer AppImage (portable, no install needed)
for a in assets:
    n = a["name"].lower()
    if n.endswith(".appimage") and ("x86_64" in n or "amd64" in n or "linux" in n):
        print(a["browser_download_url"])
        sys.exit(0)

# Fallback: any Linux tarball/zip
for a in assets:
    n = a["name"].lower()
    if "linux" in n and not n.endswith((".sha256", ".sig")):
        print(a["browser_download_url"])
        sys.exit(0)

sys.exit(1)
PYEOF
)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "[ERROR] Could not find a Linux chiaki-ng release."
    echo "Download manually from: https://github.com/streetpea/chiaki-ng/releases"
    exit 1
fi

FILENAME=$(basename "$DOWNLOAD_URL")
echo "Downloading $FILENAME..."
curl -L --progress-bar "$DOWNLOAD_URL" -o "downloads/$FILENAME"
chmod +x "downloads/$FILENAME"
echo "chiaki-ng ready: downloads/$FILENAME"

# ── Done ──────────────────────────────────────────────────────────────────────
echo
echo "============================================"
echo "  Setup complete!"
echo
echo "  Next steps:"
echo "  1. Follow the PS4 setup in README.md"
echo "  2. Launch chiaki-ng and register your PS4:"
echo "     ./downloads/$FILENAME"
echo "  3. Run ./run-linux.sh before opening chiaki-ng"
echo "  4. ./run-linux.sh to start playing"
echo
echo "  NOTE: If the virtual controller fails with a"
echo "  permissions error, log out and back in to"
echo "  activate the 'input' group membership."
echo "============================================"
