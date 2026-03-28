#!/usr/bin/env bash
# codesnap setup for Ubuntu 24.04+ (Wayland + GNOME)
# Fixed for GNOME Wayland compatibility

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/codesnap"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info() { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
error() { echo -e "${RED}✗${NC} $*"; exit 1; }
step() { echo -e "\n${CYAN}▸${NC} $*"; }

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       codesnap installer v2          ║"
echo "║      (GNOME Wayland fixed)           ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check if running on Wayland
if [[ "$XDG_SESSION_TYPE" != "wayland" ]]; then
    warn "Not running on Wayland. This script is optimized for Wayland."
    warn "If you're on X11, the selection tool may not work properly."
fi

# System deps
step "Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y \
    grim \
    slurp \
    wl-clipboard \
    tesseract-ocr \
    tesseract-ocr-eng \
    libnotify-bin \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    gnome-screenshot

info "System packages installed"

# Check if gnome-screenshot is available (fallback)
if command -v gnome-screenshot &> /dev/null; then
    info "GNOME screenshot tool available (will be used as fallback)"
else
    warn "gnome-screenshot not found - manual coordinate input may be needed"
fi

# uv
step "Setting up uv..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    source "$HOME/.cargo/env" 2>/dev/null || true
fi
info "uv ready"

# Python env
step "Creating uv virtual environment..."
mkdir -p "$APP_DIR"
cd "$APP_DIR"
rm -rf .venv
uv venv --python 3.12
source .venv/bin/activate

uv pip install --upgrade pip
uv pip install pytesseract pillow autopep8

info "Python packages installed"

deactivate

# Copy the Python script
step "Installing codesnap.py..."
cp "$SCRIPT_DIR/codesnap.py" "$APP_DIR/codesnap.py"
chmod +x "$APP_DIR/codesnap.py"
info "Python script installed to $APP_DIR/codesnap.py"

# Create launcher script
step "Installing codesnap launcher..."
mkdir -p "$INSTALL_DIR"

cat > "$INSTALL_DIR/codesnap" << 'EOF'
#!/usr/bin/env bash
APP_DIR="$HOME/.local/share/codesnap"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
exec "$APP_DIR/.venv/bin/python" "$APP_DIR/codesnap.py" "$@"
EOF

chmod +x "$INSTALL_DIR/codesnap"
info "Launcher installed to $INSTALL_DIR/codesnap"

# Hotkey (GNOME)
step "Registering hotkey Super+Shift+L..."
BINDING_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/codesnap/"
EXISTING=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings 2>/dev/null || echo "@as []")

if ! echo "$EXISTING" | grep -q "codesnap"; then
    if [ "$EXISTING" = "@as []" ]; then
        NEW_LIST="['$BINDING_PATH']"
    else
        NEW_LIST="${EXISTING%]}, '$BINDING_PATH']"
    fi
    gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "$NEW_LIST"
fi

gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" name "codesnap"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" command "$INSTALL_DIR/codesnap"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" binding "<Super><Shift>l"

info "Hotkey registered"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║ ✅ codesnap v2 installed successfully!                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📸 How to use:"
echo "   1. Press Super + Shift + L"
echo "   2. Select code area (try slurp first, then GNOME screenshot)"
echo "   3. Code is automatically copied to clipboard"
echo "   4. Paste with Ctrl+V"
echo ""
echo "🔧 If slurp doesn't work, the script will automatically:"
echo "   • Fall back to GNOME's screenshot tool"
echo "   • Or prompt for manual coordinates"
echo ""
echo "Test it now: codesnap"
echo ""

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "💡 Add to PATH (if not already):"
    echo '   export PATH="$HOME/.local/bin:$PATH"'
    echo ""
fi